# VoteCollege — Enhanced Online Voting System

A Django-based college election platform with 5 premium enhancements.

---

## ✅ New Features

### 1. 📊 Charts on Results Page
- **Doughnut (Pie) Chart** — shows vote share per candidate
- **Bar Chart** — shows absolute vote counts side-by-side
- Correct **percentage calculation** for every candidate
- Live tooltips on hover via Chart.js 4.x

### 2. 📩 Email OTP Verification
- On registration, a **6-digit OTP** is sent to the student's college email
- OTP expires in **10 minutes**
- Students cannot log in until email is verified
- "Resend OTP" button available
- `EMAIL_BACKEND = console` in development (OTP printed to terminal); switch to SMTP for production

### 3. ⏰ Election Start & End Time
- `ElectionStatus` now has `start_time` and `end_time` fields
- Election **automatically opens and closes** based on these timestamps
- If fields are blank, manual `is_open` toggle is used (original behaviour preserved)
- Dashboard shows status badge: **Upcoming / Open / Ended / Closed**
- Dashboard shows the scheduled window: `d M, H:i → d M, H:i`

### 4. 🔍 Audit Log
- Every security-relevant event is recorded in `AuditLog`:
  | Action | Trigger |
  |--------|---------|
  | `LOGIN` | Successful login |
  | `LOGOUT` | Logout |
  | `VOTE` | Vote cast |
  | `REGISTER` | New account created |
  | `OTP_SENT` | OTP emailed |
  | `OTP_VERIFY` | OTP successfully verified |
  | `OTP_FAILED` | Wrong/expired OTP entered |
  | `ACCESS_DENY` | Bad password, unverified voter, closed election attempt |
- Stores: **student**, **IP address**, **timestamp**, **details**
- Staff-only page at `/audit-log/` with live client-side filtering
- Also visible in Django Admin → Audit Logs

### 5. 📈 Dashboard Statistics
- Stats row at the top of the student dashboard:
  - **Total Voters** — all active non-staff students
  - **Votes Cast** — distinct voters who have voted at least once
  - **Candidates** — total registered candidates
  - **Participation %** — animated progress bar
- Per-position vote counts shown on each position card

---

## 🚀 Setup

```bash
cd votes_enhanced
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Email configuration
Development (default) — OTP is printed to the terminal:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Production — edit `voting_system/settings.py`:
```python
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Election scheduling (Admin Panel)
1. Go to `/admin/` → **Election Status**
2. Set **Start time** and **End time** (use the datetime pickers)
3. Save — the election will automatically open/close at the set times

---

## 📁 Changed Files

| File | Change |
|------|--------|
| `election/models.py` | Added `email_verified`, `otp`, `otp_created_at` to Student; `start_time`, `end_time` to ElectionStatus; new `AuditLog` model |
| `election/views.py` | OTP flow, auto-timing, audit logging, dashboard stats, results percentages |
| `election/forms.py` | Added `OTPVerificationForm`; email uniqueness check |
| `election/urls.py` | Added `verify_otp`, `resend_otp`, `audit_log` routes |
| `election/admin.py` | Enhanced admin for all new models/fields |
| `election/utils.py` | **New** — OTP generation, email sending, IP helper, audit logger |
| `election/migrations/0003_enhanced_features.py` | **New** — DB migration for all new fields |
| `templates/election/verify_otp.html` | **New** — OTP entry page |
| `templates/election/audit_log.html` | **New** — Staff audit log viewer |
| `templates/election/results.html` | Dual charts + leaderboard + percentage + overall stats |
| `templates/election/dashboard.html` | Stats row + time window display |
| `templates/base.html` | Audit Log nav link; improved alerts |
| `static/css/style.css` | Full redesign covering all new UI components |
| `voting_system/settings.py` | Email backend config; TIME_ZONE → Asia/Kolkata |
