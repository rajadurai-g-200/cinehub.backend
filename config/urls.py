
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Authentication: OTP, Google login, profile, users
    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    # Movies: creator upload, movie listing, details, approval
    path(
        "api/movies/",
        include("movies.urls"),
    ),
]

# Serve uploaded movie logos and video files in development.
# This is for development only, not production deployment.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
