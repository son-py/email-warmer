-- Add created_at to peer_pool so it matches the SQLAlchemy model
ALTER TABLE peer_pool
  ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();
