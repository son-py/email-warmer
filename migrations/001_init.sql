-- Enable UUID generator
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS inbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  label text NOT NULL,
  provider text NOT NULL,
  smtp_host text, smtp_port int, smtp_user text, smtp_pass text, use_tls bool,
  imap_host text, imap_port int, imap_user text, imap_pass text, use_ssl bool,
  daily_target int DEFAULT 20,
  warmup_state jsonb DEFAULT '{}'::jsonb,
  active bool DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS peer_pool (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  inbox_id uuid REFERENCES inbox(id) ON DELETE CASCADE,
  peer_email text NOT NULL,
  weight int DEFAULT 1
);

CREATE TABLE IF NOT EXISTS send_log (
  id bigserial PRIMARY KEY,
  inbox_id uuid REFERENCES inbox(id) ON DELETE CASCADE,
  to_email text NOT NULL,
  subject text NOT NULL,
  body text NOT NULL,
  sent_at timestamptz DEFAULT now(),
  provider_message_id text,
  success bool DEFAULT true,
  error text
);

CREATE TABLE IF NOT EXISTS read_log (
  id bigserial PRIMARY KEY,
  inbox_id uuid REFERENCES inbox(id) ON DELETE CASCADE,
  provider_message_id text,
  action text,
  at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_send_log_inbox_date ON send_log (inbox_id, sent_at);
