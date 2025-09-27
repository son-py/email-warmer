import datetime as dt, random
from sqlalchemy import select, func, and_
from .db import SessionLocal
from .models import Inbox, PeerPool, SendLog
from .services.scheduler import today_send_plan
from .services.composer import make_message
from .services.imap_reader import poll_and_reply
from .email_providers.smtp import send_email

def sent_count_today(db, inbox_id):
    today = dt.datetime.utcnow().date()
    start = dt.datetime(today.year, today.month, today.day, tzinfo=dt.timezone.utc)
    q = select(func.count(SendLog.id)).where(and_(SendLog.inbox_id==inbox_id, SendLog.sent_at >= start))
    return db.execute(q).scalar() or 0

def weighted_choice(peers):
    emails = [p[0] for p in peers]
    weights = [max(1, p[1]) for p in peers]
    return random.choices(emails, weights=weights, k=1)[0]

def run_once():
    now = dt.datetime.utcnow()
    minutes_now = now.hour*60 + now.minute
    db = SessionLocal()
    try:
        inboxes = db.execute(select(Inbox).where(Inbox.active==True)).scalars().all()
        for inbox in inboxes:
            plan = today_send_plan(inbox.daily_target)
            due = [m for m in plan if m <= minutes_now]
            already = sent_count_today(db, inbox.id)
            to_send = max(0, len(due) - already)

            peers = db.execute(select(PeerPool).where(PeerPool.inbox_id==inbox.id)).scalars().all()
            peer_pairs = [(p.peer_email, p.weight) for p in peers] or []

            for _ in range(to_send):
                if not peer_pairs:
                    break
                to_email = weighted_choice(peer_pairs)
                subject, body = make_message()
                ok, err, msgid = True, None, None
                try:
                    msgid = send_email(inbox, to_email, subject, body)
                except Exception as e:
                    ok, err = False, str(e)[:500]
                db.add(SendLog(inbox_id=inbox.id, to_email=to_email, subject=subject,
                               body=body, success=ok, error=err, provider_message_id=msgid))
                db.commit()

            # Read/reply pass
            try:
                poll_and_reply(inbox, [p[0] for p in peer_pairs])
            except Exception:
                pass
    finally:
        db.close()

if __name__ == "__main__":
    run_once()
