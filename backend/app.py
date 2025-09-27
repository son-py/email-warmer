import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from .db import SessionLocal
from .models import Inbox, PeerPool
from .migrate import *  # run migrations at import if not yet applied
from .settings import APP_ADMIN_TOKEN

def require_admin(x_admin_token: str | None):
    if not x_admin_token or x_admin_token != APP_ADMIN_TOKEN:
        raise HTTPException(401, "Unauthorized")

app = FastAPI(title="Email Warmer")

class InboxCreate(BaseModel):
    label: str
    provider: str  # 'smtp'
    daily_target: int | None = 20
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_pass: str | None = None
    use_tls: bool | None = True
    imap_host: str | None = None
    imap_port: int | None = None
    imap_user: str | None = None
    imap_pass: str | None = None
    use_ssl: bool | None = True

class PeerCreate(BaseModel):
    inbox_id: str
    peer_email: str
    weight: int | None = 1

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/inboxes")
def list_inboxes(x_admin_token: str | None = Header(default=None)):
    require_admin(x_admin_token)
    db = SessionLocal()
    try:
        inboxes = db.execute(select(Inbox)).scalars().all()
        return [{"id": str(i.id), "label": i.label, "daily_target": i.daily_target, "active": i.active} for i in inboxes]
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
        p = PeerPool(inbox_id=payload.inbox_id, peer_email=payload.peer_email, weight=payload.weight or 1)
        db.add(p)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
