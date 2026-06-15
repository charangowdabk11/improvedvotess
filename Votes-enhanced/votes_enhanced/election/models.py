from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ─── Student (Custom User) ────────────────────────────────────────────────────
class Student(AbstractUser):
    student_id   = models.CharField(max_length=20, unique=True)
    department   = models.CharField(max_length=100)
    is_verified  = models.BooleanField(default=False)           # admin-verified voter

    # Email OTP verification
    email_verified  = models.BooleanField(default=False)
    otp             = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at  = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.student_id})"

    def is_otp_valid(self):
        """OTP expires after 10 minutes."""
        if not self.otp or not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).seconds < 600


# ─── Position ─────────────────────────────────────────────────────────────────
class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ─── Candidate ────────────────────────────────────────────────────────────────
class Candidate(models.Model):
    name       = models.CharField(max_length=100)
    position   = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    photo      = models.ImageField(upload_to='candidates/')
    manifesto  = models.TextField()
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.position.name}"


# ─── Vote ─────────────────────────────────────────────────────────────────────
class Vote(models.Model):
    voter     = models.ForeignKey(Student, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position  = models.ForeignKey(Position, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'position')

    def __str__(self):
        return f"{self.voter.username} voted for {self.candidate.name}"


# ─── Election Status ──────────────────────────────────────────────────────────
class ElectionStatus(models.Model):
    title              = models.CharField(max_length=200, default="College Election 2026")
    is_open            = models.BooleanField(default=False)          # manual override
    results_published  = models.BooleanField(default=False)
    start_time         = models.DateTimeField(blank=True, null=True)  # auto-open
    end_time           = models.DateTimeField(blank=True, null=True)  # auto-close

    class Meta:
        verbose_name_plural = "Election Status"

    def __str__(self):
        return f"{self.title} — {'Open' if self.currently_open() else 'Closed'}"

    def currently_open(self):
        """Returns True if election is open right now (time-window or manual flag)."""
        now = timezone.now()
        if self.start_time and self.end_time:
            return self.start_time <= now <= self.end_time
        return self.is_open

    def get_status_label(self):
        now = timezone.now()
        if self.start_time and self.end_time:
            if now < self.start_time:
                return "upcoming"
            elif now > self.end_time:
                return "ended"
            else:
                return "open"
        return "open" if self.is_open else "closed"


# ─── Audit Log ────────────────────────────────────────────────────────────────
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN',       'Login'),
        ('LOGOUT',      'Logout'),
        ('VOTE',        'Vote Cast'),
        ('REGISTER',    'Registration'),
        ('OTP_SENT',    'OTP Sent'),
        ('OTP_VERIFY',  'OTP Verified'),
        ('OTP_FAILED',  'OTP Failed'),
        ('ACCESS_DENY', 'Access Denied'),
    ]

    student    = models.ForeignKey(Student, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='audit_logs')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details    = models.TextField(blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        who = self.student.username if self.student else "anonymous"
        return f"[{self.get_action_display()}] {who} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
