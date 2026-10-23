from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):

    ROLE_CHOICES = (
        ("USER", "User"),
        ("CREATOR", "Creator"),
    )

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="USER",
    )

    def get_display_role(self):
        if self.is_staff or self.is_superuser:
            return "ADMIN"

        return self.role

    def __str__(self):
        return f"{self.username} - {self.get_display_role()}"


class EmailOTP(models.Model):

    email = models.EmailField(db_index=True)

    otp = models.CharField(max_length=6)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        default=timezone.now,
    )

    def is_expired(self):
        if self.expires_at is not None:
            return timezone.now() >= self.expires_at

        # Fallback for older OTP records without an expiry timestamp.
        return timezone.now() >= (
            self.created_at + timedelta(minutes=5)
        )

    def __str__(self):
        return self.email


class UserActivity(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="activity",
    )

    last_seen = models.DateTimeField(
        default=timezone.now,
    )

    is_online = models.BooleanField(
        default=False,
    )

    def update_activity(self):
        self.last_seen = timezone.now()
        self.is_online = True
        self.save(
            update_fields=["last_seen", "is_online"]
        )

    def check_online(self):
        return timezone.now() <= (
            self.last_seen + timedelta(minutes=5)
        )

    def __str__(self):
        return f"{self.user.username} - {self.is_online}"
