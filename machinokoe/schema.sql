-- ============================================================
--  まちのコエ — 地域課題解決プラットフォーム
--  データベース設計 (PostgreSQL / Supabase)
--
--  設計方針
--   1. 匿名性：氏名はDBに持たず、表示名は user_id から導出した通称のみ
--   2. 重複投票の防止：votes に (issue_id, user_id) の UNIQUE 制約
--   3. 賛同数はトリガで非正規化カラムに反映（一覧のソートを高速に）
--   4. RLS を全テーブルで有効化し、削除・改竄をDB層で防ぐ
--   5. 収支は誰でも読める（透明性）。書き込みは運営のみ
-- ============================================================

create extension if not exists "pgcrypto";

-- ---------- 列挙型 ----------
create type issue_category as enum (
  'facility',   -- 公共施設
  'road',       -- 道路・交通
  'env',        -- 環境・衛生
  'safety',     -- 防災・安全
  'welfare',    -- 福祉・子育て
  'other'
);

create type issue_status as enum (
  'open',       -- 賛同を集めている
  'ready',      -- 閾値到達・提案書を生成できる
  'submitted',  -- 行政へ提出済み
  'answered',   -- 行政から回答あり
  'resolved',   -- 解決
  'hidden'      -- 通報により非表示
);

create type comment_kind as enum ('comment', 'solution');


-- ============================================================
--  profiles : auth.users の公開プロフィール
--  ※ 氏名・メールは auth.users 側にのみ存在し、ここには持たない
-- ============================================================
create table profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  handle       text not null,                       -- 例）住民 A7（自動採番、本名は入れない）
  district     text,                                -- 任意：居住地区（市区町村レベルまで）
  is_admin     boolean not null default false,
  created_at   timestamptz not null default now()
);


-- ============================================================
--  places : 課題を紐づける地点
-- ============================================================
create table places (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  lat          double precision not null,
  lng          double precision not null,
  created_at   timestamptz not null default now()
);
create index places_geo_idx on places (lat, lng);


-- ============================================================
--  issues : 課題
-- ============================================================
create table issues (
  id            uuid primary key default gen_random_uuid(),
  author_id     uuid not null references profiles(id) on delete cascade,
  category      issue_category not null,
  place_id      uuid references places(id) on delete set null,
  lat           double precision,                   -- 地点マスタに無い任意座標
  lng           double precision,
  title         text not null check (char_length(title) between 5 and 60),
  body          text not null check (char_length(body)  between 15 and 2000),
  status        issue_status not null default 'open',

  vote_count    integer not null default 0,         -- トリガで同期（非正規化）
  comment_count integer not null default 0,         -- トリガで同期（非正規化）
  report_count  integer not null default 0,

  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),

  check (place_id is not null or (lat is not null and lng is not null))
);

create index issues_rank_idx     on issues (status, vote_count desc, created_at desc);
create index issues_category_idx on issues (category, vote_count desc);
create index issues_author_idx   on issues (author_id);
-- 全文検索（日本語は pg_bigm / pgroonga が使えるなら差し替える）
create index issues_search_idx   on issues using gin (to_tsvector('simple', title || ' ' || body));


-- ============================================================
--  votes : 賛同（アップボート）
--  UNIQUE 制約が重複投票の防止そのもの
-- ============================================================
create table votes (
  issue_id   uuid not null references issues(id) on delete cascade,
  user_id    uuid not null references profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (issue_id, user_id)
);
create index votes_user_idx on votes (user_id);


-- ============================================================
--  comments : 議論・解決策の提案
-- ============================================================
create table comments (
  id         uuid primary key default gen_random_uuid(),
  issue_id   uuid not null references issues(id) on delete cascade,
  author_id  uuid not null references profiles(id) on delete cascade,
  parent_id  uuid references comments(id) on delete cascade,   -- 1段だけ返信を許す
  kind       comment_kind not null default 'comment',
  body       text not null check (char_length(body) between 5 and 2000),
  is_hidden  boolean not null default false,
  created_at timestamptz not null default now()
);
create index comments_issue_idx on comments (issue_id, created_at);


-- ============================================================
--  proposals : 自動生成された提案書（行政提出用）
-- ============================================================
create table proposals (
  id             uuid primary key default gen_random_uuid(),
  issue_id       uuid not null references issues(id) on delete cascade,
  serial_no      text not null unique,              -- 例）MK-2026-0007
  vote_snapshot  integer not null,                  -- 生成時点の賛同数（後から動いても証跡は残す）
  summary        text not null,                     -- 議論の要約
  pdf_url        text,                              -- Storage 上のPDF
  submitted_to   text,                              -- 提出先（例：〇〇市 道路課）
  submitted_at   timestamptz,
  response_body  text,                              -- 行政からの回答
  responded_at   timestamptz,
  created_at     timestamptz not null default now()
);
create index proposals_issue_idx on proposals (issue_id);


-- ============================================================
--  reports : 通報（個人情報・誹謗中傷など）
-- ============================================================
create table reports (
  id          uuid primary key default gen_random_uuid(),
  issue_id    uuid references issues(id) on delete cascade,
  comment_id  uuid references comments(id) on delete cascade,
  reporter_id uuid not null references profiles(id) on delete cascade,
  reason      text not null,
  created_at  timestamptz not null default now(),
  check (num_nonnulls(issue_id, comment_id) = 1)
);


-- ============================================================
--  透明性：寄付と運営費
--  どちらも「誰でも読める」ことが理念上の要件
-- ============================================================
create table donations (
  id            uuid primary key default gen_random_uuid(),
  donor_label   text not null default '匿名',        -- 公開名。本名を入れる運用はしない
  amount        integer not null check (amount > 0),
  provider      text,                               -- stripe / paypal など
  provider_ref  text unique,                        -- 決済IDで冪等性を担保
  received_at   timestamptz not null default now()
);

create table expenses (
  id          uuid primary key default gen_random_uuid(),
  item        text not null,                        -- 例）Supabase / ドメイン
  note        text,
  amount      integer not null check (amount >= 0),
  incurred_on date not null,
  created_at  timestamptz not null default now()
);

create table budget_goals (
  month       date primary key,                     -- 月初日で管理
  goal_amount integer not null check (goal_amount > 0)
);


-- ============================================================
--  トリガ：賛同数・コメント数の同期
-- ============================================================
create or replace function sync_vote_count() returns trigger
language plpgsql security definer as $$
declare
  target uuid := coalesce(new.issue_id, old.issue_id);
  n integer;
begin
  select count(*) into n from votes where issue_id = target;
  update issues
     set vote_count = n,
         status = case
                    when status in ('submitted','answered','resolved','hidden') then status
                    when n >= 50 then 'ready'::issue_status
                    else 'open'::issue_status
                  end,
         updated_at = now()
   where id = target;
  return null;
end $$;

create trigger trg_votes_sync
after insert or delete on votes
for each row execute function sync_vote_count();


create or replace function sync_comment_count() returns trigger
language plpgsql security definer as $$
declare
  target uuid := coalesce(new.issue_id, old.issue_id);
begin
  update issues
     set comment_count = (select count(*) from comments where issue_id = target and not is_hidden)
   where id = target;
  return null;
end $$;

create trigger trg_comments_sync
after insert or delete or update of is_hidden on comments
for each row execute function sync_comment_count();


-- ============================================================
--  ビュー：透明性ダッシュボード用
-- ============================================================
create or replace view v_monthly_finance as
select
  m.month,
  coalesce(g.goal_amount, 0)                                    as goal_amount,
  coalesce(d.total, 0)                                          as donation_total,
  coalesce(e.total, 0)                                          as expense_total,
  coalesce(d.total, 0) - coalesce(e.total, 0)                   as balance,
  coalesce(d.cnt, 0)                                            as donation_count
from (
  select distinct date_trunc('month', received_at)::date as month from donations
  union
  select distinct date_trunc('month', incurred_on)::date        from expenses
) m
left join budget_goals g on g.month = m.month
left join (
  select date_trunc('month', received_at)::date as month, sum(amount) total, count(*) cnt
  from donations group by 1
) d on d.month = m.month
left join (
  select date_trunc('month', incurred_on)::date as month, sum(amount) total
  from expenses group by 1
) e on e.month = m.month;


-- ============================================================
--  Row Level Security
--   公開読み取り × 本人のみ書き込み × 削除は禁止（改竄防止）
-- ============================================================
alter table profiles     enable row level security;
alter table places       enable row level security;
alter table issues       enable row level security;
alter table votes        enable row level security;
alter table comments     enable row level security;
alter table proposals    enable row level security;
alter table reports      enable row level security;
alter table donations    enable row level security;
alter table expenses     enable row level security;
alter table budget_goals enable row level security;

-- 読み取り：原則すべて公開（reports のみ運営限定）
create policy "read all" on profiles     for select using (true);
create policy "read all" on places       for select using (true);
create policy "read all" on issues       for select using (status <> 'hidden');
create policy "read all" on votes        for select using (true);
create policy "read all" on comments     for select using (not is_hidden);
create policy "read all" on proposals    for select using (true);
create policy "read all" on donations    for select using (true);
create policy "read all" on expenses     for select using (true);
create policy "read all" on budget_goals for select using (true);

create policy "admin reads reports" on reports for select
  using (exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin));

-- 書き込み：ログイン済みの本人のみ
create policy "self insert" on issues for insert
  with check (auth.uid() = author_id);
create policy "self update" on issues for update
  using (auth.uid() = author_id) with check (auth.uid() = author_id);

create policy "self vote"   on votes for insert with check (auth.uid() = user_id);
create policy "self unvote" on votes for delete using (auth.uid() = user_id);

create policy "self comment" on comments for insert with check (auth.uid() = author_id);
create policy "self report"  on reports  for insert with check (auth.uid() = reporter_id);

create policy "self profile" on profiles for update
  using (auth.uid() = id) with check (auth.uid() = id);

-- 収支・提案書の書き込みは運営のみ（Edge Function / service_role 経由）
create policy "admin writes" on donations    for all
  using (exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin));
create policy "admin writes" on expenses     for all
  using (exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin));
create policy "admin writes" on budget_goals for all
  using (exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin));
create policy "admin writes" on proposals    for all
  using (exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin));

-- issues / comments に DELETE ポリシーを作らない＝誰も削除できない。
-- 不適切な投稿は status='hidden' / is_hidden=true で運営が伏せる運用とする。
