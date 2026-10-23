from django.urls import path

from .views import (
    send_otp,
    verify_otp,
    google_login,
    profile_setup,
    current_user,
    heartbeat,
    logout_user,
    admin_statistics,
    admin_users,
)

app_name = "accounts"

urlpatterns = [
    # Email OTP authentication
    path(
        "send-otp/",
        send_otp,
        name="send_otp",
    ),
    
    path(
        "profile-setup/",
        profile_setup,
        name="profile_setup",
    ),
    path(
        "verify-otp/",
        verify_otp,
        name="verify_otp",
    ),

    # Google authentication
    path(
        "google/",
        google_login,
        name="google_login",
    ),

    # User profile
    path(
        "profile-setup/",
        profile_setup,
        name="profile_setup",
    ),
    path(
        "me/",
        current_user,
        name="current_user",
    ),

    # Session / account status
    path(
        "heartbeat/",
        heartbeat,
        name="heartbeat",
    ),
    path(
        "logout/",
        logout_user,
        name="logout_user",
    ),

    # Admin dashboard
    path(
        "admin/statistics/",
        admin_statistics,
        name="admin_statistics",
    ),
    path(
        "admin/users/",
        admin_users,
        name="admin_users",
    ),
]