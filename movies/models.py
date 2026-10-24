from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Movie(models.Model):

    # Available video quality options
    QUALITY_CHOICES = (
        ("HD", "HD"),
        ("FULL_HD", "Full HD"),
    )

    # Available languages
    LANGUAGE_CHOICES = (
        ("TAMIL", "Tamil"),
        ("ENGLISH", "English"),
    )

    # Movie approval status
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    # Movie creator
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movies",
    )

    # Movie information
    title = models.CharField(max_length=200)
    release_date = models.DateField()
    director = models.CharField(max_length=200)
    starring = models.CharField(max_length=500)
    genres = models.CharField(max_length=300)

    # Movie rating: 0.0 to 10.0
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )

    # Language
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
    )

    # Default movie quality
    quality = models.CharField(
        max_length=20,
        choices=QUALITY_CHOICES,
    )

    # Movie poster or logo
    logo = models.ImageField(
        upload_to="movie_logos/",
        blank=True,
        null=True,
    )

    # Main movie video
    movie_file = models.FileField(
        upload_to="movies/videos/",
        blank=True,
        null=True,
    )

    # Admin approval status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # Optional message from admin
    admin_message = models.TextField(
        blank=True,
        null=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class MovieQuality(models.Model):

    # Available video resolutions
    QUALITY_CHOICES = (
        ("1080p", "1080p"),
        ("720p", "720p"),
        ("480p", "480p"),
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="quality_files",
    )

    quality = models.CharField(
        max_length=10,
        choices=QUALITY_CHOICES,
    )

    file = models.FileField(
        upload_to="movie_quality/",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movie.title} - {self.quality}"
