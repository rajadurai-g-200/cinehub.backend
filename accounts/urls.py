from django.urls import path

from .views import (
    send_otp,
    verify_otp,
    profile_setup
)


urlpatterns = [

    # Send OTP
    path(
        "send-otp/",
        send_otp,
        name="send_otp"
    ),

    # Verify OTP
    path(
        "verify-otp/",
        verify_otp,
        name="verify_otp"
    ),

    # Profile setup
    path(
        "profile-setup/",
        profile_setup,
        name="profile_setup"
    ),

]