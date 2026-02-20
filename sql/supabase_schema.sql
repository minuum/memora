-- Stateful AI Workspace schema for Supabase
-- Apply in Supabase SQL Editor (project-level)

create extension if not exists pgcrypto;

create table if not exists public.ai_sessions (
  id bigint generated always as identity primary key,
  server_id text not null,
  session_id text not null,
  last_updated timestamptz not null default now(),
  summary text not null default '',
  conversation jsonb not null default '[]'::jsonb,
  snapshot jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (server_id, session_id)
);

create index if not exists ai_sessions_server_updated_idx
  on public.ai_sessions (server_id, last_updated desc);

create table if not exists public.ai_longterm (
  id uuid primary key default gen_random_uuid(),
  server_id text not null,
  content_hash text not null,
  text text not null,
  metadata jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  unique (server_id, content_hash)
);

create index if not exists ai_longterm_server_updated_idx
  on public.ai_longterm (server_id, updated_at desc);

-- Optional RLS baseline: service-role key can bypass RLS.
alter table public.ai_sessions enable row level security;
alter table public.ai_longterm enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'ai_sessions' and policyname = 'service_role_all_sessions'
  ) then
    create policy service_role_all_sessions
      on public.ai_sessions
      for all
      using (auth.role() = 'service_role')
      with check (auth.role() = 'service_role');
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'ai_longterm' and policyname = 'service_role_all_longterm'
  ) then
    create policy service_role_all_longterm
      on public.ai_longterm
      for all
      using (auth.role() = 'service_role')
      with check (auth.role() = 'service_role');
  end if;
end $$;
