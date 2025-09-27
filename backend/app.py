# backend/app.py
import os
import asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from .db import SessionLocal
from .models import Inbox, PeerPool
from .worker import run_once  # used by /run-now and optional self-scheduler

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
APP_ADMIN_TOKEN = os.getenv("APP_ADMIN_TOKEN", "changeme")
SELF_SCHEDULER = os.getenv("SELF_SCHEDULER", "0").lower() in {"1", "true", "yes"}
SCHEDULE_SECONDS = int(os.getenv("SCHEDULE_SECONDS", "600"))  # 10 minutes default

def require_admin(x_admin_token: str | None):
    if not x_admin_token or x_admin_token != APP_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(title="Email Warmer")

# Friendly landing so the root URL isn't a 404
@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({
        "ok": True,
        "try": [
            "GET /health",
            "GET /inboxes   (requires header X-Admin-Token)",
            "POST /inboxes  (requires header X-Admin-Token)",
            "POST /peers    (requires header X-Admin-Token)",
            "POST /run-now  (requires header X-Admin-Token)"
        ],
        "docs": "/docs"
    })

@app.get("/health")
def health():
    return {"ok": True}

# -------------------------------------------------------------------
# Schemas
# -------------------------------------------------------------------
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

class PeerCreate(BaseModel):
    inbox_id: str
    peer_email: str
    weight: int | None = 1

# -------------------------------------------------------------------
# Admin API
# -------------------------------------------------------------------
@app.get("/inboxes")
def list_inboxes(x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    db = SessionLocal()
    try:
        inboxes = db.execute(select(Inbox)).scalars().all()
        return [
            {
                "id": str(i.id),
                "label": i.label,
                "daily_target": i.daily_target,
                "active": i.active
            }
            for i in inboxes
        ]
    finally:
        db.close()

@app.post("/inboxes")
def create_inbox(payload: InboxCreate, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    db = SessionLocal()
    try:
        data = payload.model_dump()
        i = Inbox(**data)
        db.add(i)
        db.commit()
        db.refresh(i)
        return {"id": str(i.id), "label": i.label}
    finally:
        db.close()

@app.post("/peers")
def add_peer(payload: PeerCreate, x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    db = SessionLocal()
    try:
        p = PeerPool(
            inbox_id=payload.inbox_id,
            peer_email=payload.peer_email,
            weight=payload.weight or 1
        )
        db.add(p)
        db.commit()
        return {"ok": True}
    finally:
        db.close()

# -------------------------------------------------------------------
# Free trigger endpoint (works great with GitHub Actions)
# -------------------------------------------------------------------
@app.post("/run-now")
def run_now(x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    # run synchronously; it’s fast and avoids extra complexity
    run_once()
    return {"ok": True}

# -------------------------------------------------------------------
# Optional self-scheduler (FREE) - enable with SELF_SCHEDULER=1
# Keep your Render free instance awake using a pinger (e.g., UptimeRobot on /health)
# -------------------------------------------------------------------
@app.on_event("startup")
async def _maybe_start_scheduler():
    if not SELF_SCHEDULER:
        return

    async def loop():
        while True:
            try:
                # run the blocking worker in a thread so the server stays responsive
                await asyncio.to_thread(run_once)
            except Exception as e:
                print("worker error:", e)
            await asyncio.sleep(SCHEDULE_SECONDS)

    asyncio.create_task(loop())
