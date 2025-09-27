import random

SUBJECTS = [
    "Quick check-in", "Following up", "Short note", "Ping", "Thoughts?",
    "Looping you in", "Small question", "Re: earlier"
]
BODIES = [
    "Testing deliverability—do you see this?",
    "Thanks for the earlier note. Reply when free.",
    "Quick update from my side—looks good.",
    "Appreciate your help—will follow up tomorrow.",
    "Confirming this reaches the inbox okay."
]

def make_message(thread_snippet: str | None = None):
    subject = random.choice(SUBJECTS)
    body = random.choice(BODIES)
    if thread_snippet and random.random() < 0.6:
        body = f"> {thread_snippet}\n\n{body}"
    return subject, body
