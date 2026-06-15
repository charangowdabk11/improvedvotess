"""Utility helpers: OTP generation, email sending, IP extraction, audit logging."""
import random
import string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


# ─── OTP ─────────────────────────────────────────────────────────────────────
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(student, otp):
    """Send OTP to student's registered email."""
    subject = "VoteCollege — Email Verification OTP"
    body = f"""Hello {student.get_full_name() or student.username},

Your One-Time Password (OTP) for VoteCollege email verification is:

    {otp}

This OTP is valid for 10 minutes. Do not share it with anyone.

If you did not register on VoteCollege, please ignore this email.

— VoteCollege Administration
"""
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [student.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log to console in development
        print(f"[EMAIL ERROR] Could not send OTP to {student.email}: {e}")
        # In development with console backend, the email body is printed to terminal
        return False


def assign_otp(student):
    """Generate a fresh OTP, attach it to the student, and persist."""
    otp = generate_otp()
    student.otp = otp
    student.otp_created_at = timezone.now()
    student.save(update_fields=['otp', 'otp_created_at'])
    return otp


# ─── IP Address ──────────────────────────────────────────────────────────────
def get_client_ip(request):
    """Extract the real client IP, respecting X-Forwarded-For header."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─── Audit Logging ───────────────────────────────────────────────────────────
def log_action(request, action, student=None, details=''):
    """Write a row to the AuditLog table."""
    from .models import AuditLog
    AuditLog.objects.create(
        student=student,
        action=action,
        ip_address=get_client_ip(request),
        details=details,
    )
