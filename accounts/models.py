from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from datetime import timedelta


class User(AbstractUser):

    ROLE_CHOICES = (
        ("USER", "User"),
        ("CREATOR", "Creator"),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="USER"
    )

    def __str__(self):

        return f"{self.username} - {self.role}"


class EmailOTP(models.Model):

    email = models.EmailField()

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    def is_expired(self):

        return timezone.now() > (
            self.created_at +
            timedelta(minutes=5)
        )

    def __str__(self):

        return self.email