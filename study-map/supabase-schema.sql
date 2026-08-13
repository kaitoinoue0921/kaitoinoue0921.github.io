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
  -- 5軸の評価（1〜5）。星ごとの意味は index.html の AXES.scale に定義してある。
  -- ax_quiet   = 静音性
  -- ax_seat    = 座席・姿勢の快適さ
  -- ax_privacy = 周囲の集中度・ピア効果（列名は歴史的経緯で"privacy"のまま。
  --              旧「人目」から意味を再定義したもので、列は作り直していない）
  -- ax_refresh = 息抜きのしやすさ（新設）
  -- ax_aircon  = 空調・空間（旧「空調」から評価範囲を拡張）
  -- ax_power / ax_wifi / ax_water は廃止列。電源・Wi-Fiは事実ベースの
  -- facilities（jsonb）バッジに移行し、水は評価対象から外したため、
  -- アプリはこの3列にはもう値を送らない（過去データの参照用に残してある）。
  ax_quiet    smallint check (ax_quiet   between 1 and 5),
  ax_power    smallint check (ax_power   between 1 and 5),
  ax_wifi     smallint check (ax_wifi    between 1 and 5),
  ax_seat     smallint check (ax_seat    between 1 and 5),
  ax_privacy  smallint check (ax_privacy between 1 and 5),
  ax_aircon   smallint check (ax_aircon  between 1 and 5),
  ax_water    smallint check (ax_water   between 1 and 5),
  ax_refresh  smallint check (ax_refresh between 1 and 5),
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
  -- 「行ったが勉強できなかった／評価できない」という報告用。true のときは
  -- ax_* を全部NULLにして送る（星評価はしていない）ので、上のNOT NULL制約を
  -- 外しておく必要がある。スコア計算（avgAxes/score100）はこの行を無視する。
  cant_study  boolean not null default false,
  created_at  timestamptz not null default now()
);

-- すでにこのテーブルをNOT NULL付きで作ってしまっている場合は、次を1回だけ流すこと
-- （cant_study=true の投稿はax_*を送らないため、NOT NULLのままだと保存に失敗する）:
alter table public.reviews alter column ax_quiet   drop not null;
alter table public.reviews alter column ax_power   drop not null;
alter table public.reviews alter column ax_wifi    drop not null;
alter table public.reviews alter column ax_seat    drop not null;
alter table public.reviews alter column ax_privacy drop not null;
alter table public.reviews alter column ax_aircon  drop not null;
alter table public.reviews alter column ax_water   drop not null;

-- 5軸への改修（息抜きのしやすさを新設）で、既存の本番DBに次を1回だけ流すこと:
alter table public.reviews add column if not exists ax_refresh smallint check (ax_refresh between 1 and 5);

alter table public.reviews add column if not exists cant_study boolean not null default false;

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

-- 更新・削除（プロトタイプ用：匿名でも可）。
-- これが無い間はUPDATE/DELETEが「成功したように見えて0件しか更新されない」
-- （HTTPは2xxを返すのに反映されない）という気づきにくい失敗をする。
drop policy if exists spots_update   on public.spots;
drop policy if exists spots_delete   on public.spots;
drop policy if exists reviews_delete on public.reviews;
create policy spots_update   on public.spots   for update using (true) with check (true);
create policy spots_delete   on public.spots   for delete using (true);
create policy reviews_delete on public.reviews for delete using (true);

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
