-- =========================================================
-- スタディスポットMAP — Supabase スキーマ
-- Supabase の SQL Editor にそのまま貼って実行してください。
-- =========================================================

-- ---------- スポット ----------
create table if not exists public.spots (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  pref        text not null default '栃木県',
  city        text,
  category    text,
  address     text,
  lat         double precision not null,
  lng         double precision not null,
  hours_wd    text,          -- 平日の利用時間  例: 9:00–19:00
  hours_we    text,          -- 土日祝の利用時間
  closed_days text,          -- 休館日
  fee         text,
  note        text,
  -- 設備の「事実」。{"wifi":1,"power":0,...} の形で入れる。
  -- 1=あり 0=なし キーなし=不明 の3状態があるので、列に割らず jsonb 1本で持つ。
  facilities  jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

-- すでに facilities 列なしでこのスキーマを実行してしまっている場合は、次を1回流すこと:
--   alter table public.spots add column if not exists facilities jsonb not null default '{}'::jsonb;
alter table public.spots add column if not exists facilities jsonb not null default '{}'::jsonb;

create index if not exists spots_pref_city_idx on public.spots (pref, city);

-- ---------- 口コミ ----------
create table if not exists public.reviews (
  id          uuid primary key default gen_random_uuid(),
  spot_id     uuid not null references public.spots(id) on delete cascade,
  user_name   text,
  -- 7軸の評価（1〜5）。星ごとの意味は index.html の AXES.scale に定義してある。
  ax_quiet    smallint not null check (ax_quiet   between 1 and 5),
  ax_power    smallint not null check (ax_power   between 1 and 5),
  ax_wifi     smallint not null check (ax_wifi    between 1 and 5),
  ax_seat     smallint not null check (ax_seat    between 1 and 5),
  ax_privacy  smallint not null check (ax_privacy between 1 and 5),
  ax_aircon   smallint not null check (ax_aircon  between 1 and 5),
  ax_water    smallint not null check (ax_water   between 1 and 5),
  -- 「アクセス」の軸は廃止した。地図を見れば位置は分かるうえ、
  -- 近い/遠いは見る人の家がどこかで変わるので、場所の性質の評価にならないため。
  -- すでにこのスキーマを ax_access 付きで実行してしまっている場合は、
  -- アプリが値を送らなくなり NOT NULL 違反で投稿が全部失敗する。次を1回だけ流すこと:
  --   alter table public.reviews alter column ax_access drop not null;
  comment     text,
  -- 訪問した曜日区分・時間帯・混み具合（空き状況ヒートマップの元データ）
  visit_day   text     check (visit_day in ('wd','we')),
  visit_slot  smallint check (visit_slot between 0 and 5),   -- 0:9-11 1:11-13 2:13-15 3:15-17 4:17-19 5:19-21
  visit_level smallint check (visit_level between 1 and 3),  -- 1:混雑 2:ふつう 3:空き
  created_at  timestamptz not null default now()
);

create index if not exists reviews_spot_idx on public.reviews (spot_id);

-- ---------- 応援メッセージ（各作品の応援セクションから届く） ----------
create table if not exists public.messages (
  id         uuid primary key default gen_random_uuid(),
  name       text,                     -- 未入力なら「名無し」扱い
  body       text not null check (char_length(body) between 1 and 1000),
  work       text check (char_length(work) <= 40),   -- どの作品宛てか（support.js の作品ID）
  kind       text not null default 'comment'
             check (kind in ('comment','support')),  -- support = 投げ銭したうえでの一言
  approved   boolean not null default false,         -- 公開は承認制
  created_at timestamptz not null default now()
);

-- すでにテーブルを作ったあとで work 列を足す場合はこの1行だけ実行すればよい
alter table public.messages add column if not exists work text check (char_length(work) <= 40);

create index if not exists messages_created_idx on public.messages (created_at desc);
create index if not exists messages_work_idx    on public.messages (work, created_at desc);

-- =========================================================
-- 行レベルセキュリティ（RLS）
-- ---------------------------------------------------------
-- 下の設定は「誰でも読める・誰でも書ける」プロトタイプ用です。
-- このまま一般公開するとスパムや荒らしを止める手段がありません。
-- 公開前に必ず、下の「本番向け」のコメントに従って
-- ログイン必須（authenticated）＋承認フローに切り替えてください。
-- =========================================================
alter table public.spots   enable row level security;
alter table public.reviews enable row level security;

-- 読み取りは全員に許可
drop policy if exists spots_read   on public.spots;
drop policy if exists reviews_read on public.reviews;
create policy spots_read   on public.spots   for select using (true);
create policy reviews_read on public.reviews for select using (true);

-- 書き込み（プロトタイプ用：匿名でも投稿可）
drop policy if exists spots_insert   on public.spots;
drop policy if exists reviews_insert on public.reviews;
create policy spots_insert   on public.spots   for insert with check (true);
create policy reviews_insert on public.reviews for insert with check (true);

-- ---------- 応援メッセージ ----------
-- 投稿は誰でもできるが、表示されるのは承認済みのものだけ。
-- 承認は Supabase の Table Editor で approved を true にする。
alter table public.messages enable row level security;

drop policy if exists messages_read   on public.messages;
drop policy if exists messages_insert on public.messages;

create policy messages_read on public.messages
  for select using (approved);

create policy messages_insert on public.messages
  for insert with check (approved = false);   -- 自分で承認済みにして投稿することはできない

-- 更新・削除は誰にも許可しない（ポリシーを作らなければ拒否される）

-- ---------------------------------------------------------
-- 本番向けに切り替えるとき:
--
--   drop policy spots_insert   on public.spots;
--   drop policy reviews_insert on public.reviews;
--
--   alter table public.spots   add column author uuid references auth.users(id) default auth.uid();
--   alter table public.reviews add column author uuid references auth.users(id) default auth.uid();
--   alter table public.spots   add column approved boolean not null default false;
--
--   create policy spots_insert on public.spots
--     for insert to authenticated with check (author = auth.uid());
--   create policy reviews_insert on public.reviews
--     for insert to authenticated with check (author = auth.uid());
--
--   -- 承認済みのスポットだけを一般公開する
--   drop policy spots_read on public.spots;
--   create policy spots_read on public.spots
--     for select using (approved or author = auth.uid());
--
--   -- 1人1スポット1件までに制限する場合
--   create unique index reviews_one_per_user on public.reviews (spot_id, author);
-- ---------------------------------------------------------
