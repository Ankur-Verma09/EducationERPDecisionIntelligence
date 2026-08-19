-- The application must never connect as the migration owner because the
-- PostgreSQL bootstrap user is a superuser and therefore bypasses RLS.
CREATE ROLE education_erp_app
    LOGIN
    PASSWORD 'local-runtime-only'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOBYPASSRLS;

GRANT CONNECT ON DATABASE education_erp TO education_erp_app;
GRANT USAGE ON SCHEMA public TO education_erp_app;

ALTER DEFAULT PRIVILEGES FOR ROLE education_erp IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO education_erp_app;
ALTER DEFAULT PRIVILEGES FOR ROLE education_erp IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO education_erp_app;
