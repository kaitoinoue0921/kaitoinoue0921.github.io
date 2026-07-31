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
  created_at  timestamptz not null default now()
);

create index if not exists spots_pref_city_idx on public.spots (pref, city);

-- ---------- 口コミ ----------
create table if not exists public.reviews (
  id          uuid primary key default gen_random_uuid(),
  spot_id     uuid not null references public.spots(id) on delete cascade,
  user_name   text,
  -- 8軸の評価（1〜5）
  ax_quiet    smallint not null check (ax_quiet   between 1 and 5),
  ax_power    smallint not null check (ax_power   between 1 and 5),
  ax_wifi     smallint not null check (ax_wifi    between 1 and 5),
  ax_seat     smallint not null check (ax_seat    between 1 and 5),
  ax_privacy  smallint not null check (ax_privacy between 1 and 5),
  ax_aircon   smallint not null check (ax_aircon  between 1 and 5),
  ax_access   smallint not null check (ax_access  between 1 and 5),
  ax_water    smallint not null check (ax_water   between 1 and 5),
  comment     text,
  -- 訪問した曜日区分・時間帯・混み具合（空き状況ヒートマップの元データ）
  visit_day   text     check (visit_day in ('wd','we')),
  visit_slot  smallint check (visit_slot between 0 and 5),   -- 0:9-11 1:11-13 2:13-15 3:15-17 4:17-19 5:19-21
  visit_level smallint check (visit_level between 1 and 3),  -- 1:混雑 2:ふつう 3:空き
  created_at  timestamptz not null default now()
);

create index if not exists reviews_spot_idx on public.reviews (spot_id);

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
