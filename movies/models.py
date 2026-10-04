from django.db import models
from django.conf import settings


class Movie(models.Model):

    QUALITY_CHOICES = (
        ("HD", "HD"),
        ("FULL_HD", "Full HD"),
    )

    LANGUAGE_CHOICES = (
        ("TAMIL", "Tamil"),
        ("ENGLISH", "English"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    # Creator
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movies"
    )

    # Movie basic information
    title = models.CharField(
        max_length=200
    )

    release_date = models.DateField()

    director = models.CharField(
        max_length=200
    )

    starring = models.CharField(
        max_length=500
    )

    genres = models.CharField(
        max_length=300
    )

    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES
    )

    quality = models.CharField(
        max_length=20,
        choices=QUALITY_CHOICES
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0
    )

    # Movie logo / poster
    logo = models.ImageField(
        upload_to="movie_logos/",
        blank=True,
        null=True
    )

    # Main movie file
    movie_file = models.FileField(
        upload_to="movies/",
        blank=True,
        null=True
    )

    # Admin approval
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    admin_message = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title
    
class MovieQuality(models.Model):

    QUALITY_CHOICES = (
        ("1080p", "1080p"),
        ("720p", "720p"),
        ("480p", "480p"),
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="quality_files"
    )

    quality = models.CharField(
        max_length=10,
        choices=QUALITY_CHOICES
    )

    file = models.FileField(
        upload_to="movie_quality/"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.movie.title} - {self.quality}"