-- Lo mínimo de Supabase para correr las migraciones en un Postgres común:
-- el esquema auth con auth.uid() y los roles de la página. auth.uid() lee el
-- mismo dato que en Supabase (el "sub" del token), así que los tests se
-- identifican igual que la página real.

create schema if not exists auth;

create or replace function auth.uid() returns uuid
language sql stable as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

grant usage on schema auth to public;

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'anon') then
        create role anon nologin;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
        create role authenticated nologin;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'service_role') then
        create role service_role nologin bypassrls;
    end if;
end;
$$;

grant usage on schema public to anon, authenticated, service_role;
