# backend/models.py
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey, func, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class Inbox(Base):
    __tablename__ = "inbox"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    label = Column(String(255), nullable=False, unique=True)
    provider = Column(String(50), nullable=False, default="smtp")
    daily_target = Column(Integer, nullable=False, default=20)
    active = Column(Boolean, nullable=False, default=True)

    # SMTP
    smtp_host = Column(String(255))
    smtp_port = Column(Integer)
    smtp_user = Column(String(255))
    smtp_pass = Column(String(255))
    use_tls = Column(Boolean, default=True)

    # IMAP
    imap_host = Column(String(255))
    imap_port = Column(Integer)
    imap_user = Column(String(255))
    imap_pass = Column(String(255))
    use_ssl = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    peers = relationship("PeerPool", back_populates="inbox", cascade="all, delete-orphan")

class PeerPool(Base):
    __tablename__ = "peer_pool"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="CASCADE"), nullable=False)
    peer_email = Column(String(255), nullable=False)
    weight = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inbox = relationship("Inbox", back_populates="peers")

class SendLog(Base):
    __tablename__ = "send_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="SET NULL"))
    to_email = Column(String(255))
    subject = Column(String(512))
    body = Column(Text)
    provider_message_id = Column(String(255))
    success = Column(Boolean, default=True)
    error = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

class ReadLog(Base):
    __tablename__ = "read_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="SET NULL"))
    message_id = Column(String(255))
    action = Column(String(50))  # opened/starred/replied
    at = Column(DateTime(timezone=True), server_default=func.now())
