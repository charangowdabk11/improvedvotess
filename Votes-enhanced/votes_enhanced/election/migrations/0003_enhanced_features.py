from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0002_electionstatus_results_published'),
    ]

    operations = [
        # Add OTP fields to Student
        migrations.AddField(
            model_name='student',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='student',
            name='otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # Add start_time / end_time to ElectionStatus
        migrations.AddField(
            model_name='electionstatus',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True,
                                       help_text='Leave blank to control manually via is_open'),
        ),
        migrations.AddField(
            model_name='electionstatus',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True,
                                       help_text='Leave blank to control manually via is_open'),
        ),

        # Create AuditLog model
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('LOGIN',       'Login'),
                        ('LOGOUT',      'Logout'),
                        ('VOTE',        'Vote Cast'),
                        ('REGISTER',    'Registration'),
                        ('OTP_SENT',    'OTP Sent'),
                        ('OTP_VERIFY',  'OTP Verified'),
                        ('OTP_FAILED',  'OTP Failed'),
                        ('ACCESS_DENY', 'Access Denied'),
                    ],
                    max_length=20,
                )),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('details',    models.TextField(blank=True)),
                ('timestamp',  models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
