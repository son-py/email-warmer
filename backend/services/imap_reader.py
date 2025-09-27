from imapclient import IMAPClient
from email import message_from_bytes
from .composer import make_message
from ..email_providers.smtp import send_email
import random

def poll_and_reply(inbox, peer_emails: list[str], reply_rate=0.4, star_rate=0.2):
    """
    Mark peer messages as read, sometimes star, sometimes reply.
    """
    if not (inbox.imap_host and inbox.imap_user and inbox.imap_pass):
        return

    with IMAPClient(inbox.imap_host, port=inbox.imap_port or 993, ssl=bool(inbox.use_ssl)) as imap:
        imap.login(inbox.imap_user, inbox.imap_pass)
        imap.select_folder("INBOX", readonly=False)
        uids = imap.search(["UNSEEN"])
        if not uids:
            return

        fetched = imap.fetch(uids, ["RFC822"])
        for uid, data in fetched.items():
            raw = data.get(b"RFC822", b"")
            if not raw:
                continue
            msg = message_from_bytes(raw)
            from_addr = (msg.get("From") or "").lower()

            if any(p.lower() in from_addr for p in peer_emails):
                imap.add_flags(uid, [b"\\Seen"])
                if star_rate and random.random() < star_rate:
                    try:
                        imap.add_flags(uid, [b"\\Flagged"])
                    except Exception:
                        pass

                if reply_rate and random.random() < reply_rate:
                    to_addr = msg.get("Reply-To") or msg.get("From")
                    subj = msg.get("Subject") or ""
                    subject, body = make_message(subj)
                    try:
                        send_email(inbox, to_addr, subject, body)
                    except Exception:
                        pass

        imap.logout()
