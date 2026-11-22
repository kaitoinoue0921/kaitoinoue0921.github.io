-- =========================================================
-- コメント欄（/comments/comments.js）— Supabase スキーマ
-- Supabase の SQL Editor に丸ごと貼って 1 回実行する。何度流しても壊れない。
--
-- 投稿はすぐ表示される。通報が 3 件たまると自動で隠れる。
-- 消したいときは Table Editor で hidden を true にする（行を消すと返信も消える）。
-- =========================================================

create table if not exists public.comments (
  id         uuid primary key default gen_random_uuid(),
  page       text not null check (char_length(page) between 1 and 160),  -- どのページ・どの施設か
  parent_id  uuid references public.comments(id) on delete cascade,     -- 返信先（null なら親コメント）
  name       text check (char_length(name) <= 30),                      -- 空なら「名無し」
  body       text not null check (char_length(body) between 1 and 800),
  reports    int  not null default 0,
  hidden     boolean not null default false,
  created_at timestamptz not null default now(),
  -- URL を含む投稿は弾く（宣伝スパム対策）
  constraint comments_no_url check (body !~* '(https?://|www\.|\.(com|net|jp|xyz|ru)/)')
);

create index if not exists comments_page_idx on public.comments (page, created_at);

alter table public.comments enable row level security;

drop policy if exists comments_read   on public.comments;
drop policy if exists comments_insert on public.comments;

-- 読めるのは隠れていないものだけ
create policy comments_read on public.comments
  for select using (not hidden and reports < 3);

-- 誰でも投稿できるが、通報数や hidden を自分で決めて送ることはできない
create policy comments_insert on public.comments
  for insert with check (reports = 0 and hidden = false);

-- 更新・削除のポリシーは作らない（＝閲覧者は誰も書き換えられない）

-- ---------- 通報 ----------
-- 閲覧者は update できないので、通報数を 1 増やすだけの関数を用意する
create or replace function public.report_comment(cid uuid)
returns void language sql security definer set search_path = public as $$
  update public.comments set reports = reports + 1 where id = cid;
$$;
grant execute on function public.report_comment(uuid) to anon, authenticated;

-- ---------- 連投よけ ----------
-- サイト全体で 1 分に 15 件、同じページに同じ本文の重複は断る
create or replace function public.comments_guard()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.comments where created_at > now() - interval '1 minute') >= 15 then
    raise exception 'too many comments, try later';
  end if;
  if exists (select 1 from public.comments
             where page = new.page and body = new.body
               and created_at > now() - interval '1 day') then
    raise exception 'duplicate comment';
  end if;
  return new;
end $$;

drop trigger if exists comments_guard on public.comments;
create trigger comments_guard before insert on public.comments
  for each row execute function public.comments_guard();
