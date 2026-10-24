import logging
import random
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailOTP


logger = logging.getLogger(__name__)
User = get_user_model()


# ==================================================
# HELPERS
# ==================================================

def get_user_role(user):
    if user.is_superuser or user.is_staff:
        return "ADMIN"

    return str(getattr(user, "role", "USER")).upper()


def user_response_data(user):
    email = getattr(user, "email", "") or ""

    return {
        "id": user.id,
        "username": (
            getattr(user, "username", "")
            or email.split("@")[0]
        ),
        "email": email,
        "role": get_user_role(user),
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
    }


def jwt_response(user):
    """
    Issue CineHub JWT tokens after successful authentication.
    """
    refresh = RefreshToken.for_user(user)

    return {
        "message": "Login successful.",
        "user": user_response_data(user),
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def create_user_for_email(email):
    """
    Create a Django user for an email address.
    Adapt this helper if your custom User model requires
    additional mandatory fields.
    """
    username = email.split("@")[0]

    has_username = any(
        field.name == "username"
        for field in User._meta.fields
    )

    if has_username:
        if User.objects.filter(username=username).exists():
            username = f"{username}_{secrets.token_hex(3)}"

        return User.objects.create_user(
            username=username,
            email=email,
            password=secrets.token_urlsafe(32),
        )

    return User.objects.create_user(
        email=email,
        password=secrets.token_urlsafe(32),
    )


def is_admin_user(user):
    return (
        user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or get_user_role(user) == "ADMIN"
        )
    )


# ==================================================
# GOOGLE LOGIN
# POST /api/auth/google/
# Body: {"credential": "Google ID token"}
# ==================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    credential = request.data.get("credential")

    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "") or ""
    client_id = client_id.strip()

    if not credential:
        return Response(
            {"message": "Google credential is missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not client_id:
        return Response(
            {"message": "Google login is not configured."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        google_user = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            audience=client_id,
        )
    except ValueError:
        return Response(
            {"message": "Google token is invalid or expired."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception:
        logger.exception("Google token verification failed.")
        return Response(
            {"message": "Google verification service is unavailable."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    email = (google_user.get("email") or "").strip().lower()

    if not email or google_user.get("email_verified") is not True:
        return Response(
            {"message": "Please use a verified Google account."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user = User.objects.filter(email__iexact=email).first()
        is_new_user = user is None

        if is_new_user:
            user = create_user_for_email(email)

        if not user.is_active:
            return Response(
                {"message": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response_data = jwt_response(user)
        response_data["is_new_user"] = is_new_user

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception:
        logger.exception("Google login user creation failed.")
        return Response(
            {"message": "Unable to complete Google login."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# ==================================================
# SEND OTP
# POST /api/auth/send-otp/
# Body: {"email": "user@gmail.com"}
# ==================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    email = (request.data.get("email") or "").strip().lower()

    if not email:
        return Response(
            {"message": "Email address is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp = f"{random.randint(0, 999999):06d}"

    try:
        EmailOTP.objects.filter(
            email__iexact=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        send_mail(
            subject="Your CineHub verification code",
            message=(
                f"Your CineHub OTP is {otp}. "
                "It expires in 5 minutes."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {"message": "OTP sent successfully."},
            status=status.HTTP_200_OK,
        )

    except Exception:
        # Do not expose OTPs or SMTP credentials in API responses.
        logger.exception("Unable to send CineHub OTP.")

        return Response(
            {"message": "Unable to send OTP. Check email configuration."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==================================================
# VERIFY OTP
# POST /api/auth/verify-otp/
# Body: {"email": "...", "otp": "...", "role": "USER"}
# ==================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    email = (request.data.get("email") or "").strip().lower()
    otp = (request.data.get("otp") or "").strip()

    requested_role = (
        request.data.get("role") or "USER"
    ).strip().upper()

    if not email or not otp:
        return Response(
            {"message": "Email and OTP are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if requested_role not in ("USER", "CREATOR"):
        return Response(
            {"message": "Invalid account role."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    record = EmailOTP.objects.filter(
        email__iexact=email,
        otp=otp,
    ).first()

    if record is None:
        return Response(
            {"message": "Invalid OTP."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if record.expires_at <= timezone.now():
        record.delete()

        return Response(
            {"message": "OTP expired. Request a new OTP."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.filter(
            email__iexact=email
        ).first()

        if user is None:
            user = create_user_for_email(email)

        if not user.is_active:
            return Response(
                {"message": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Never grant ADMIN through public OTP verification.
        if hasattr(user, "role"):
            current_role = get_user_role(user)

            if current_role not in ("ADMIN", "CREATOR"):
                user.role = requested_role
                user.save(update_fields=["role"])

        record.delete()

        return Response(
            jwt_response(user),
            status=status.HTTP_200_OK,
        )

    except Exception:
        logger.exception("OTP verification failed.")

        return Response(
            {"message": "Unable to complete login."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==================================================
# PROFILE SETUP
# POST /api/auth/profile-setup/
# ==================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def profile_setup(request):
    user = request.user
    data = request.data

    updated_fields = []

    for field in ("first_name", "last_name"):
        if field in data and hasattr(user, field):
            setattr(user, field, str(data[field]).strip())
            updated_fields.append(field)

    if updated_fields:
        user.save(update_fields=updated_fields)

    return Response(
        {
            "message": "Profile updated successfully.",
            "user": user_response_data(user),
        },
        status=status.HTTP_200_OK,
    )


# ==================================================
# CURRENT USER
# GET /api/auth/me/
# ==================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response(
        {"user": user_response_data(request.user)},
        status=status.HTTP_200_OK,
    )


# ==================================================
# HEARTBEAT
# GET /api/auth/heartbeat/
# ==================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def heartbeat(request):
    return Response(
        {
            "message": "CineHub connection is active.",
            "authenticated": True,
            "user_id": request.user.id,
        },
        status=status.HTTP_200_OK,
    )


# ==================================================
# LOGOUT
# POST /api/auth/logout/
# Body: {"refresh": "CineHub refresh token"}
# ==================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    refresh_token = request.data.get("refresh")

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except Exception:
            logger.warning(
                "Refresh token could not be blacklisted.",
                exc_info=True,
            )

    return Response(
        {
            "message": (
                "Logged out. Clear access and refresh tokens "
                "in the frontend."
            )
        },
        status=status.HTTP_200_OK,
    )


# Backwards-compatible import name.
logout = logout_user


# ==================================================
# ADMIN USERS
# GET /api/auth/admin/users/
# ==================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_users(request):
    if not is_admin_user(request.user):
        return Response(
            {"message": "Admin permission required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    users = User.objects.all().order_by("-date_joined")
    results = []

    for user in users:
        joined = getattr(user, "date_joined", None)
        last_login = getattr(user, "last_login", None)

        results.append(
            {
                **user_response_data(user),
                "date_joined": (
                    joined.isoformat() if joined else None
                ),
                "last_seen": (
                    last_login.isoformat() if last_login else None
                ),
                "is_online": False,
            }
        )

    return Response(results, status=status.HTTP_200_OK)


# ==================================================
# ADMIN STATISTICS
# GET /api/auth/admin/statistics/
# ==================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_statistics(request):
    if not is_admin_user(request.user):
        return Response(
            {"message": "Admin permission required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    from movies.models import Movie

    all_users = User.objects.all()
    user_fields = {
        field.name for field in User._meta.fields
    }

    total_creators = 0

    if "role" in user_fields:
        total_creators = all_users.filter(
            role__iexact="CREATOR"
        ).count()

    return Response(
        {
            "total_users": all_users.filter(
                is_staff=False,
                is_superuser=False,
            ).count(),
            "total_creators": total_creators,
            "online_users": 0,
            "online_creators": 0,
            "total_movies": Movie.objects.count(),
            "pending_movies": Movie.objects.filter(
                status="PENDING"
            ).count(),
            "approved_movies": Movie.objects.filter(
                status="APPROVED"
            ).count(),
            "rejected_movies": Movie.objects.filter(
                status="REJECTED"
            ).count(),
        },
        status=status.HTTP_200_OK,
    )
