from django.contrib import admin
from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "creator",
        "release_date",
        "language",
        "quality",
        "rating",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "language",
        "quality",
    )

    search_fields = (
        "title",
        "director",
        "starring",
        "genres",
        "creator__username",
        "creator__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )