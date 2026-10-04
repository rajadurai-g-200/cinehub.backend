import random

from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from rest_framework.decorators import (
    api_view,
    permission_classes
)

from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response

from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailOTP


# =========================================================
# USER MODEL
# =========================================================

User = get_user_model()


# =========================================================
# SEND OTP
# =========================================================

@api_view(["POST"])
def send_otp(request):

    # Get email from frontend
    email = request.data.get("email")

    print("====================================")
    print("SEND OTP REQUEST")
    print("EMAIL:", email)
    print("====================================")

    # Check email
    if not email:
        return Response(
            {
                "message": "Email is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean email
    email = email.strip().lower()

    # Check Gmail
    if not email.endswith("@gmail.com"):
        return Response(
            {
                "message": "Please enter a valid Gmail address."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate 6 digit OTP
    otp = str(
        random.randint(100000, 999999)
    )

    print("GENERATED OTP:", otp)

    # Delete old unverified OTP
    EmailOTP.objects.filter(
        email=email,
        is_verified=False
    ).delete()

    # Create new OTP
    EmailOTP.objects.create(
        email=email,
        otp=otp
    )

    # Send email
    try:

        send_mail(
            subject="CineHub Login OTP",

            message=f"""
Welcome to CineHub!

Your CineHub login OTP is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

CineHub Team
""",

            from_email=None,

            recipient_list=[
                email
            ],

            fail_silently=False
        )

        print("OTP EMAIL SENT SUCCESSFULLY")

    except Exception as e:

        print("EMAIL ERROR:", e)

        return Response(
            {
                "message": "Unable to send OTP."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {
            "message": "OTP sent successfully."
        },
        status=status.HTTP_200_OK
    )


# =========================================================
# VERIFY OTP
# =========================================================

@api_view(["POST"])
def verify_otp(request):

    # Get email
    email = request.data.get("email")

    print("====================================")
    print("VERIFY OTP REQUEST")
    print("EMAIL:", email)

    # Check email
    if not email:
        return Response(
            {
                "message": "Email is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean email
    email = email.strip().lower()

    # Get OTP
    otp = request.data.get("otp")

    print("OTP:", otp)

    # Check OTP
    if not otp:
        return Response(
            {
                "message": "OTP is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Convert OTP to string
    otp = str(otp).strip()

    # Find OTP
    otp_object = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        is_verified=False
    ).last()

    print("OTP OBJECT:", otp_object)

    # Invalid OTP
    if not otp_object:

        print("INVALID OTP")

        return Response(
            {
                "message": "Invalid OTP."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check expiry
    if otp_object.is_expired():

        print("OTP EXPIRED")

        otp_object.delete()

        return Response(
            {
                "message": "OTP expired. Please request a new OTP."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Mark OTP verified
    otp_object.is_verified = True
    otp_object.save()

    print("OTP VERIFIED SUCCESSFULLY")

    # =====================================================
    # CREATE / GET USER
    # =====================================================

    try:

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0]
            }
        )

        print("USER:", user)
        print("USER CREATED:", created)

    except Exception as e:

        print("USER ERROR:", e)

        return Response(
            {
                "message": "Unable to create user."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # =====================================================
    # CREATE JWT
    # =====================================================

    try:

        refresh = RefreshToken.for_user(
            user
        )

        access_token = str(
            refresh.access_token
        )

        refresh_token = str(
            refresh
        )

        print("JWT CREATED SUCCESSFULLY")

    except Exception as e:

        print("JWT ERROR:", e)

        return Response(
            {
                "message": "Unable to create login token."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    print("LOGIN SUCCESS")
    print("====================================")

    # =====================================================
    # RESPONSE
    # =====================================================

    return Response(
        {
            "message": "Login successful",

            "access": access_token,

            "refresh": refresh_token,

            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        },

        status=status.HTTP_200_OK
    )


# =========================================================
# PROFILE SETUP
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def profile_setup(request):

    # Get name
    username = request.data.get(
        "username"
    )

    # Get role
    role = request.data.get(
        "role"
    )

    print("PROFILE SETUP")
    print("USERNAME:", username)
    print("ROLE:", role)

    # Check name
    if not username:

        return Response(
            {
                "message": "Name is required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean name
    username = username.strip()

    if not username:

        return Response(
            {
                "message": "Name cannot be empty."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check role
    if role not in [
        "USER",
        "CREATOR"
    ]:

        return Response(
            {
                "message": "Invalid role. Choose USER or CREATOR."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Current logged-in user
    user = request.user

    # Update user
    user.username = username
    user.role = role

    user.save()

    return Response(
        {
            "message": "Profile setup completed.",

            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        },

        status=status.HTTP_200_OK
    )