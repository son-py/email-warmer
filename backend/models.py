from sqlalchemy import Column, Integer, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .db import Base

class Inbox(Base):
    __tablename__ = "inbox"
    id = Column(UUID(as_uuid=True), primary_key=True)
    label = Column(Text, nullable=False)
    provider = Column(Text, nullable=False)  # 'smtp' (Outlook/Zoho/etc.)

    # SMTP creds
    smtp_host = Column(Text)
    smtp_port = Column(Integer)
    smtp_user = Column(Text)
    smtp_pass = Column(Text)
    use_tls = Column(Boolean, default=True)

    # IMAP creds
    imap_host = Column(Text)
    imap_port = Column(Integer)
    imap_user = Column(Text)
    imap_pass = Column(Text)
    use_ssl = Column(Boolean, default=True)

    daily_target = Column(Integer, default=20)
    warmup_state = Column(JSONB, default={})
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    peers = relationship("PeerPool", back_populates="inbox_obj")

class PeerPool(Base):
    __tablename__ = "peer_pool"
    id = Column(UUID(as_uuid=True), primary_key=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="CASCADE"))
    peer_email = Column(Text, nullable=False)
    weight = Column(Integer, default=1)
    inbox_obj = relationship("Inbox", back_populates="peers")

class SendLog(Base):
    __tablename__ = "send_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="CASCADE"))
    to_email = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    provider_message_id = Column(Text)
    success = Column(Boolean, default=True)
    error = Column(Text)

class ReadLog(Base):
    __tablename__ = "read_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inbox_id = Column(UUID(as_uuid=True), ForeignKey("inbox.id", ondelete="CASCADE"))
    provider_message_id = Column(Text)
    action = Column(Text)  # 'read' | 'replied' | 'starred'
    at = Column(DateTime(timezone=True), server_default=func.now())
