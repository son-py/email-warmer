import smtplib, ssl, email.utils
from email.message import EmailMessage

def send_email(inbox, to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = inbox.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Message-Id"] = email.utils.make_msgid()
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(inbox.smtp_host, inbox.smtp_port) as server:
        if inbox.use_tls:
            server.starttls(context=ctx)
        server.login(inbox.smtp_user, inbox.smtp_pass)
        server.send_message(msg)
    return msg["Message-Id"]
