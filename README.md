# Email Warmer (FastAPI + Render)

Use only inboxes you control. Keep volumes low.

## Deploy (manual)
- Build: `pip install -r backend/requirements.txt`
- Start (web): `python -m backend.migrate && uvicorn backend.app:app --host 0.0.0.0 --port 10000`
- Start (cron): `python -m backend.worker`
- Env: `DATABASE_URL`, `APP_ADMIN_TOKEN`

## Outlook settings
SMTP: `smtp.office365.com:587` (TLS)  
IMAP: `outlook.office365.com:993` (SSL)

## API (header `X-Admin-Token: <token>`)
- `GET /health`
- `GET /inboxes`
- `POST /inboxes`  (create SMTP/IMAP inbox)
- `POST /peers`    (link peer to inbox)

Cron sends during 09:00–17:00 randomly and reads/replies to peer messages.
