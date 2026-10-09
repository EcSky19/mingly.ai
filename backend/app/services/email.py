"""
Sending email over plain SMTP, so any provider works (Resend, Postmark,
Amazon SES, ...) by setting SMTP_* in .env - no provider SDK, no lock-in.

With SMTP_HOST unset, nothing is sent: the email is logged and skipped. That
keeps development, tests, and production-before-an-email-account all working
without special cases elsewhere.

Sending never raises. Notification emails are a nice-to-have on top of an
action that has already succeeded (a match, a circle join), so a mail outage
must never turn that action into an error for the person using the app.
"""
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from app.core.config import settings

log = logging.getLogger("mingly.email")


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str


def send_email(email: Email) -> bool:
    """Returns True if the provider accepted the email."""
    if not settings.SMTP_HOST:
        log.info("Email skipped (SMTP_HOST not set): %r to %s", email.subject, email.to)
        return False

    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email.to
    msg["Subject"] = email.subject
    msg["Message-ID"] = make_msgid(domain="mingly.ai")
    msg.set_content(email.text)

    try:
        context = ssl.create_default_context()
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.starttls(context=context)
        with server:
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        log.exception("Email failed: %r to %s", email.subject, email.to)
        return False
