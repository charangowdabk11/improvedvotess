from django.urls import path
from . import views

urlpatterns = [
    path('',                   views.home_view,       name='home'),
    path('register/',          views.register_view,   name='register'),
    path('verify-otp/',        views.verify_otp_view, name='verify_otp'),
    path('resend-otp/',        views.resend_otp_view, name='resend_otp'),
    path('login/',             views.login_view,      name='login'),
    path('logout/',            views.logout_view,     name='logout'),
    path('dashboard/',         views.dashboard_view,  name='dashboard'),
    path('vote/<int:position_id>/', views.vote_view,  name='vote'),
    path('results/',           views.results_view,    name='results'),
    path('audit-log/',         views.audit_log_view,  name='audit_log'),
]
