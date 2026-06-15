from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from .models import Student, Position, Candidate, Vote, ElectionStatus, AuditLog
from .forms import StudentRegistrationForm, OTPVerificationForm
from .utils import assign_otp, send_otp_email, log_action
from django.contrib.auth.forms import AuthenticationForm


# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_election():
    """Always returns a single ElectionStatus object."""
    status, _ = ElectionStatus.objects.get_or_create(pk=1)
    return status


# ─── Home ─────────────────────────────────────────────────────────────────────
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


# ─── Register ─────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False
            user.save()

            otp = assign_otp(user)
            sent = send_otp_email(user, otp)

            log_action(request, 'REGISTER', student=user,
                       details=f"New registration. Email: {user.email}")
            log_action(request, 'OTP_SENT', student=user,
                       details=f"OTP sent{'(console)' if not sent else ''} to {user.email}")

            request.session['pending_verify_user_id'] = user.pk
            messages.info(
                request,
                f"Account created! A 6-digit OTP has been sent to {user.email}. "
                "Please verify to activate your account."
            )
            return redirect('verify_otp')
    else:
        form = StudentRegistrationForm()

    return render(request, 'election/register.html', {'form': form})


# ─── OTP Verification ─────────────────────────────────────────────────────────
def verify_otp_view(request):
    user_id = request.session.get('pending_verify_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    user = get_object_or_404(Student, pk=user_id)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered = form.cleaned_data['otp'].strip()

            if user.otp == entered and user.is_otp_valid():
                user.email_verified = True
                user.otp = None
                user.otp_created_at = None
                user.save(update_fields=['email_verified', 'otp', 'otp_created_at'])

                log_action(request, 'OTP_VERIFY', student=user,
                           details="Email verified successfully.")

                del request.session['pending_verify_user_id']
                login(request, user,
                      backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Email verified! Welcome to VoteCollege 🎉")
                return redirect('dashboard')
            else:
                log_action(request, 'OTP_FAILED', student=user,
                           details=f"Wrong OTP entered: {entered}")
                messages.error(request, "Invalid or expired OTP. Try again or resend.")
    else:
        form = OTPVerificationForm()

    return render(request, 'election/verify_otp.html', {'form': form, 'email': user.email})


# ─── Resend OTP ───────────────────────────────────────────────────────────────
def resend_otp_view(request):
    user_id = request.session.get('pending_verify_user_id')
    if not user_id:
        return redirect('register')

    user = get_object_or_404(Student, pk=user_id)
    otp  = assign_otp(user)
    send_otp_email(user, otp)
    log_action(request, 'OTP_SENT', student=user,
               details=f"OTP resent to {user.email}")
    messages.success(request, f"A new OTP has been sent to {user.email}.")
    return redirect('verify_otp')


# ─── Login ────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                if not user.email_verified and not user.is_staff:
                    # Re-send OTP and redirect to verify
                    otp = assign_otp(user)
                    send_otp_email(user, otp)
                    request.session['pending_verify_user_id'] = user.pk
                    messages.warning(
                        request,
                        "Your email is not verified yet. "
                        "A new OTP has been sent — please verify first."
                    )
                    return redirect('verify_otp')

                login(request, user)
                log_action(request, 'LOGIN', student=user,
                           details=f"Successful login from {request.META.get('HTTP_USER_AGENT','')[:80]}")
                return redirect('dashboard')
        else:
            # Try to identify the user for audit purposes
            username = request.POST.get('username', '')
            try:
                bad_user = Student.objects.get(username=username)
                log_action(request, 'ACCESS_DENY', student=bad_user,
                           details="Failed login attempt (wrong password).")
            except Student.DoesNotExist:
                log_action(request, 'ACCESS_DENY', details=f"Login attempt with unknown username: {username}")
    else:
        form = AuthenticationForm()

    return render(request, 'election/login.html', {'form': form})


# ─── Logout ───────────────────────────────────────────────────────────────────
def logout_view(request):
    if request.user.is_authenticated:
        log_action(request, 'LOGOUT', student=request.user)
    logout(request)
    return redirect('login')


# ─── Dashboard ───────────────────────────────────────────────────────────────
@login_required
def dashboard_view(request):
    positions      = Position.objects.all()
    election       = get_election()
    voted_positions= Vote.objects.filter(voter=request.user).values_list('position_id', flat=True)

    # ── Statistics ──
    total_voters     = Student.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()
    voters_who_voted = Vote.objects.values('voter').distinct().count()
    total_candidates = Candidate.objects.count()
    participation    = round((voters_who_voted / total_voters * 100), 1) if total_voters > 0 else 0
    total_votes_cast = Vote.objects.count()

    # Per-position vote counts for mini progress bars
    position_stats = []
    for pos in positions:
        total = Vote.objects.filter(position=pos).count()
        position_stats.append({'position': pos, 'votes': total})

    context = {
        'positions':       positions,
        'voted_positions': voted_positions,
        'election':        election,
        'is_open':         election.currently_open(),
        'is_verified':     request.user.is_verified,
        # Stats
        'total_voters':     total_voters,
        'voters_who_voted': voters_who_voted,
        'total_candidates': total_candidates,
        'participation':    participation,
        'total_votes_cast': total_votes_cast,
        'position_stats':   position_stats,
    }
    return render(request, 'election/dashboard.html', context)


# ─── Vote ─────────────────────────────────────────────────────────────────────
@login_required
def vote_view(request, position_id):
    position = get_object_or_404(Position, id=position_id)
    election = get_election()

    if not election.currently_open():
        messages.error(request, "Voting is currently closed.")
        log_action(request, 'ACCESS_DENY', student=request.user,
                   details=f"Tried to vote while election closed. Position: {position.name}")
        return redirect('dashboard')

    if not request.user.is_verified:
        messages.error(request, "Your account is not verified. Contact the administrator.")
        log_action(request, 'ACCESS_DENY', student=request.user,
                   details=f"Unverified voter attempted to vote. Position: {position.name}")
        return redirect('dashboard')

    if Vote.objects.filter(voter=request.user, position=position).exists():
        messages.warning(request, f"You have already voted for {position.name}.")
        return redirect('dashboard')

    candidates = Candidate.objects.filter(position=position)

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        if candidate_id:
            candidate = get_object_or_404(Candidate, id=candidate_id)
            Vote.objects.create(voter=request.user, candidate=candidate, position=position)
            log_action(request, 'VOTE', student=request.user,
                       details=f"Voted for '{candidate.name}' in position '{position.name}'.")
            messages.success(request, f"Your vote for {candidate.name} has been cast successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please select a candidate.")

    return render(request, 'election/vote.html', {
        'position':   position,
        'candidates': candidates,
    })


# ─── Results ─────────────────────────────────────────────────────────────────
def results_view(request):
    election = get_election()

    if not election.results_published and not (request.user.is_authenticated and request.user.is_staff):
        messages.info(request, "Results have not been published yet. Check back later.")
        return redirect('dashboard')

    positions = Position.objects.all()
    results   = []

    total_voters     = Student.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()
    voters_who_voted = Vote.objects.values('voter').distinct().count()
    overall_participation = round((voters_who_voted / total_voters * 100), 1) if total_voters > 0 else 0

    for pos in positions:
        candidates  = (Candidate.objects
                       .filter(position=pos)
                       .annotate(vote_count=Count('vote'))
                       .order_by('-vote_count'))
        total_votes = Vote.objects.filter(position=pos).count()

        # Compute percentages
        cand_data = []
        for c in candidates:
            pct = round((c.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
            cand_data.append({
                'id':         c.id,
                'name':       c.name,
                'photo_url':  c.photo.url if c.photo else '',
                'vote_count': c.vote_count,
                'percentage': pct,
            })

        results.append({
            'position':    pos,
            'candidates':  cand_data,
            'total_votes': total_votes,
        })

    context = {
        'results':               results,
        'election':              election,
        'total_voters':          total_voters,
        'voters_who_voted':      voters_who_voted,
        'overall_participation': overall_participation,
    }
    return render(request, 'election/results.html', context)


# ─── Audit Log (staff only) ───────────────────────────────────────────────────
@login_required
def audit_log_view(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('student').all()[:500]
    return render(request, 'election/audit_log.html', {'logs': logs})
