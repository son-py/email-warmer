-- migrations/002_uuid_defaults.sql
-- Ensure the function exists (Render PostgreSQL supports pgcrypto)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Give tables a server-side default so inserts from SQL also work
ALTER TABLE inbox     ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE peer_pool ALTER COLUMN id SET DEFAULT gen_random_uuid();
