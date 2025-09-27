# backend/app.py
import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone, date

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, func, and_, desc

from .db import SessionLocal
from .models import Inbox, PeerPool, SendLog, ReadLog
from .worker import run_once  # used by /run-now and optional self-scheduler

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
APP_ADMIN_TOKEN = os.getenv("APP_ADMIN_TOKEN", "changeme")
SELF_SCHEDULER = os.getenv("SELF_SCHEDULER", "0").lower() in {"1", "true", "yes"}
SCHEDULE_SECONDS = int(os.getenv("SCHEDULE_SECONDS", "600"))  # 10 minutes

def require_admin(x_admin_token: str | None):
    if not x_admin_token or x_admin_token != APP_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------------------------------------------
# App
# -------------------------------------------------------------------
app = FastAPI(title="Email Warmer")

# Same-origin UI, but leave CORS permissive if you ever host UI elsewhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------- UI -----------------------------------
STATIC_DIR = Path(__file__).parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"

@app.get("/", include_in_schema=False)
def ui_index():
    # Friendly dashboard UI at root
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    # Fallback JSON if file missing
    return JSONResponse({
        "ok": True,
        "try": [
            "GET /health",
            "GET /docs",
            "UI file not found at backend/static/index.html"
        ]
    })

@app.get("/health")
def health():
    return {"ok": True}

# ------------------------- Schemas ---------------------------------
class InboxCreate(BaseModel):
    label: str
    provider: str  # 'smtp'
    daily_target: int | None = 20
    # SMTP
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_pass: str | None = None
    use_tls: bool | None = True
    # IMAP
    imap_host: str | None = None
    imap_port: int | None = None
    imap_user: str | None = None
    imap_pass: str | None = None
    use_ssl: bool | None = True

class InboxUpdate(BaseModel):
    daily_target: int | None = None
    active: bool | None = None

class PeerCreate(BaseModel):
    inbox_id: str
    peer_email: str
    weight: int | None = 1

# ---------------------- Admin API (inboxes/peers) -------------------
@app.get("/inboxes")
def list_inboxes(x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    db = SessionLocal()
    try:
        inboxes = db.execute(select(Inbox).order_by(desc(Inbox.created_at))).scalars().all()
        return [
            {
                "id": str(i.id),
                "label": i.label,
                "provider": i.provider,
                "daily_target": i.daily_target,
                "active": i.active,
