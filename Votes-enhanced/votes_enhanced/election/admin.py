from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils import timezone
from .models import Student, Position, Candidate, Vote, ElectionStatus, AuditLog

# ── Branding ──────────────────────────────────────────────────────────────────
admin.site.site_header = "VoteCollege Administrative Portal"
admin.site.site_title  = "VoteCollege Admin"
admin.site.index_title = "Election Management & Analytics"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ('username', 'student_id', 'department', 'email',
                     'email_verified_badge', 'is_verified', 'date_joined')
    list_filter   = ('department', 'is_verified', 'email_verified')
    search_fields = ('username', 'student_id', 'email')
    ordering      = ('username',)
    readonly_fields = ('last_login', 'date_joined', 'otp', 'otp_created_at')
    actions       = ['verify_students', 'unverify_students', 'mark_email_verified']

    def email_verified_badge(self, obj):
        if obj.email_verified:
            return format_html('<span style="color:green;font-weight:bold;">✔ Verified</span>')
        return format_html('<span style="color:orange;font-weight:bold;">✘ Pending</span>')
    email_verified_badge.short_description = 'Email'

    def verify_students(self, request, queryset):
        queryset.update(is_verified=True)
    verify_students.short_description = "✔ Mark as verified voter"

    def unverify_students(self, request, queryset):
        queryset.update(is_verified=False)
    unverify_students.short_description = "✘ Remove voter verification"

    def mark_email_verified(self, request, queryset):
        queryset.update(email_verified=True, otp=None, otp_created_at=None)
    mark_email_verified.short_description = "✔ Manually verify email"

    def has_add_permission(self, request):    return request.user.is_superuser
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


@admin.register(ElectionStatus)
class ElectionStatusAdmin(admin.ModelAdmin):
    list_display  = ('title', 'status_badge', 'start_time', 'end_time', 'results_published')
    readonly_fields = ('status_badge',)

    def status_badge(self, obj):
        label = obj.get_status_label()
        colours = {
            'open':     ('green',  '✔ OPEN'),
            'closed':   ('red',    '✘ CLOSED'),
            'upcoming': ('orange', '⏳ UPCOMING'),
            'ended':    ('grey',   '■ ENDED'),
        }
        colour, text = colours.get(label, ('grey', label.upper()))
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>', colour, text
        )
    status_badge.short_description = 'Current Status'

    fieldsets = (
        ('Basic', {
            'fields': ('title', 'results_published', 'status_badge'),
        }),
        ('Manual Override', {
            'fields': ('is_open',),
            'description': 'Only used if start_time/end_time are not set.',
        }),
        ('Automatic Scheduling', {
            'fields': ('start_time', 'end_time'),
            'description': 'Set both fields to enable automatic open/close.',
        }),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_candidate_count', 'get_total_votes')

    def get_candidate_count(self, obj): return obj.candidates.count()
    get_candidate_count.short_description = 'Candidates'

    def get_total_votes(self, obj): return Vote.objects.filter(position=obj).count()
    get_total_votes.short_description = 'Votes Cast'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display  = ('name', 'position', 'department', 'get_vote_count')
    list_filter   = ('position', 'department')
    search_fields = ('name',)

    def get_vote_count(self, obj): return obj.vote_set.count()
    get_vote_count.short_description = 'Votes'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display    = ('voter', 'candidate', 'position', 'timestamp')
    list_filter     = ('position', 'timestamp')
    search_fields   = ('voter__username', 'candidate__name')
    readonly_fields = ('voter', 'candidate', 'position', 'timestamp')

    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'action_badge', 'student_link', 'ip_address', 'details_short')
    list_filter   = ('action', 'timestamp')
    search_fields = ('student__username', 'ip_address', 'details')
    readonly_fields = ('student', 'action', 'ip_address', 'details', 'timestamp')
    ordering      = ('-timestamp',)

    def action_badge(self, obj):
        colours = {
            'LOGIN':       'green',
            'LOGOUT':      'grey',
            'VOTE':        'blue',
            'REGISTER':    'purple',
            'OTP_SENT':    'orange',
            'OTP_VERIFY':  'teal',
            'OTP_FAILED':  'red',
            'ACCESS_DENY': 'darkred',
        }
        colour = colours.get(obj.action, 'black')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colour, obj.get_action_display()
        )
    action_badge.short_description = 'Action'

    def student_link(self, obj):
        if obj.student:
            return format_html(
                '<a href="/admin/election/student/{}/change/">{}</a>',
                obj.student.pk, obj.student.username
            )
        return '—'
    student_link.short_description = 'Student'

    def details_short(self, obj):
        return (obj.details[:60] + '…') if len(obj.details) > 60 else obj.details
    details_short.short_description = 'Details'

    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return request.user.is_superuser
