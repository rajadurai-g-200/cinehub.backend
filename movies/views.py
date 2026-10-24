
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Movie, MovieQuality
from .serializers import MovieUploadSerializer


logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov"}
ALLOWED_LANGUAGES = {"TAMIL", "ENGLISH"}
ALLOWED_QUALITIES = {"HD", "FULL_HD"}
ALLOWED_RATINGS = (Decimal("0.0"), Decimal("10.0"))


# =========================================================
# PERMISSIONS
# =========================================================

def is_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "role", None) == "ADMIN"
        )
    )


def is_creator(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "role", None) == "CREATOR"
        and not is_admin(user)
    )


def require_admin(request):
    if not is_admin(request.user):
        return Response(
            {"error": "Admin access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


# =========================================================
# HELPERS
# =========================================================

def upload_error(
    message,
    http_status=status.HTTP_400_BAD_REQUEST,
):
    return Response({"error": message}, status=http_status)


def absolute_file_url(request, file_field):
    if not file_field:
        return None

    try:
        return request.build_absolute_uri(file_field.url)
    except (ValueError, AttributeError):
        return None


def parse_rating(value):
    """Accept ratings from 0.0 through 10.0 with one decimal place."""

    try:
        rating = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(
            "Rating must be a number between 0.0 and 10.0."
        )

    if not rating.is_finite():
        raise ValueError("Rating must be a finite number.")

    if not ALLOWED_RATINGS[0] <= rating <= ALLOWED_RATINGS[1]:
        raise ValueError("Rating must be between 0.0 and 10.0.")

    if rating.as_tuple().exponent < -1:
        raise ValueError(
            "Rating can have only one decimal place, for example 8.5."
        )

    return rating.quantize(Decimal("0.1"))


def get_movie_queryset():
    return (
        Movie.objects.select_related("creator")
        .prefetch_related("quality_files")
    )


def movie_data(request, movie):
    """Serialize a movie and include its rating in every movie endpoint."""

    quality_files = [
        {
            "id": item.id,
            "quality": item.quality,
            "file": absolute_file_url(request, item.file),
        }
        for item in movie.quality_files.all()
    ]

    creator = movie.creator

    return {
        "id": movie.id,
        "title": movie.title,
        "release_date": movie.release_date.isoformat(),
        "director": movie.director,
        "starring": movie.starring,
        "genres": movie.genres,
        "language": movie.language,
        "quality": movie.quality,
        "rating": float(movie.rating),
        "logo": absolute_file_url(request, movie.logo),
        "movie_file": absolute_file_url(request, movie.movie_file),
        "quality_files": quality_files,
        "status": movie.status,
        "admin_message": movie.admin_message or "",
        "creator": {
            "id": creator.id,
            "username": creator.username,
            "email": creator.email,
            "role": getattr(creator, "role", "USER"),
        },
        "created_at": movie.created_at.isoformat(),
        "updated_at": movie.updated_at.isoformat(),
    }


def validate_video_file(video):
    if not video:
        return None

    extension = Path(video.name).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return (
            "Only MP4, WEBM, MKV and MOV video files are allowed."
        )

    return None


# =========================================================
# CREATE MOVIE
# =========================================================

def create_movie_from_request(request, creator, movie_status):
    data = request.data

    title = data.get("title")
    release_date = data.get("release_date")
    director = data.get("director")
    starring = data.get("starring")
    genres = data.get("genres")
    language = data.get("language")
    quality = data.get("quality") or "HD"

    # Creators may supply a rating. Admin uploads start at 0.0.
    if is_creator(creator):
        try:
            rating = parse_rating(data.get("rating", "0.0"))
        except ValueError as error:
            return upload_error(str(error))
    else:
        rating = Decimal("0.0")

    logo = request.FILES.get("logo")
    movie_file = request.FILES.get("movie_file")

    video_1080 = request.FILES.get("video_1080p")
    video_720 = request.FILES.get("video_720p")
    video_480 = request.FILES.get("video_480p")

    required_fields = {
        "title": title,
        "release_date": release_date,
        "director": director,
        "starring": starring,
        "genres": genres,
        "language": language,
    }

    for field, value in required_fields.items():
        if not value or not str(value).strip():
            return upload_error(f"{field} is required.")

    if not logo:
        return upload_error("Movie poster/logo is required.")

    if language not in ALLOWED_LANGUAGES:
        return upload_error("Language must be TAMIL or ENGLISH.")

    if quality not in ALLOWED_QUALITIES:
        return upload_error("Quality must be HD or FULL_HD.")

    try:
        parsed_date = date.fromisoformat(str(release_date))
    except (ValueError, TypeError):
        return upload_error(
            "Release date must use YYYY-MM-DD format."
        )

    videos = [
        video_1080,
        video_720,
        video_480,
        movie_file,
    ]

    for video in videos:
        error = validate_video_file(video)
        if error:
            return upload_error(error)

    if not any(videos):
        return upload_error("Upload at least one movie video file.")

    movie = None

    try:
        movie = Movie.objects.create(
            creator=creator,
            title=str(title).strip(),
            release_date=parsed_date,
            director=str(director).strip(),
            starring=str(starring).strip(),
            genres=str(genres).strip(),
            language=language,
            quality=quality,
            rating=rating,
            logo=logo,
            movie_file=movie_file,
            status=movie_status,
        )

        quality_uploads = [
            (video_1080, "1080p"),
            (video_720, "720p"),
            (video_480, "480p"),
        ]

        for video, resolution in quality_uploads:
            if video:
                MovieQuality.objects.create(
                    movie=movie,
                    quality=resolution,
                    file=video,
                )

        movie = get_movie_queryset().get(pk=movie.pk)

        return Response(
            {
                "message": "Movie uploaded successfully.",
                "status": movie.status,
                "movie": movie_data(request, movie),
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception:
        logger.exception("Movie upload failed.")

        # Avoid leaving an incomplete movie record if an upload fails.
        if movie is not None:
            movie.delete()

        return Response(
            {
                "error": (
                    "Movie upload failed. Check the Django server "
                    "terminal for details."
                )
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# =========================================================
# CREATOR OR ADMIN UPLOAD
# POST /api/movies/create/
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_movie(request):
    user = request.user

    if not (is_creator(user) or is_admin(user)):
        return Response(
            {"error": "Only creators or admins can upload movies."},
            status=status.HTTP_403_FORBIDDEN,
        )

    movie_status = "APPROVED" if is_admin(user) else "PENDING"

    return create_movie_from_request(
        request=request,
        creator=user,
        movie_status=movie_status,
    )


# =========================================================
# ADMIN UPLOAD
# POST /api/movies/admin/upload/
# =========================================================

class AdminMovieUploadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = MovieUploadSerializer

    def post(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response(
                {"error": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return create_movie_from_request(
            request=request,
            creator=request.user,
            movie_status="APPROVED",
        )


# =========================================================
# CREATOR: UPDATE OWN MOVIE RATING
# PATCH /api/movies/<movie_id>/rating/
# =========================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_movie_rating(request, movie_id):
    user = request.user

    if not is_creator(user):
        return Response(
            {"error": "Only creators can change movie ratings."},
            status=status.HTTP_403_FORBIDDEN,
        )

    movie = get_object_or_404(
        Movie,
        id=movie_id,
        creator=user,
    )

    if "rating" not in request.data:
        return upload_error("Rating is required.")

    try:
        rating = parse_rating(request.data["rating"])
    except ValueError as error:
        return upload_error(str(error))

    movie.rating = rating
    movie.save(update_fields=["rating", "updated_at"])

    movie = get_movie_queryset().get(pk=movie.pk)

    return Response(
        {
            "message": "Movie rating updated successfully.",
            "movie": movie_data(request, movie),
        },
        status=status.HTTP_200_OK,
    )


# =========================================================
# APPROVED MOVIES
# GET /api/movies/approved/
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def approved_movies(request):
    movies = (
        get_movie_queryset()
        .filter(status="APPROVED")
        .order_by("-created_at")
    )

    return Response([
        movie_data(request, movie)
        for movie in movies
    ])


# =========================================================
# MOVIE DETAILS
# GET /api/movies/<movie_id>/
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movie_details(request, movie_id):
    movie = get_object_or_404(
        get_movie_queryset(),
        id=movie_id,
    )

    allowed = (
        is_admin(request.user)
        or movie.status == "APPROVED"
        or movie.creator_id == request.user.id
    )

    if not allowed:
        return Response(
            {"error": "You cannot access this movie."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(movie_data(request, movie))


# =========================================================
# CREATOR'S MOVIES
# GET /api/movies/my/
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_movies(request):
    if not is_creator(request.user):
        return Response(
            {"error": "Creator access required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    movies = (
        get_movie_queryset()
        .filter(creator=request.user)
        .order_by("-created_at")
    )

    return Response([
        movie_data(request, movie)
        for movie in movies
    ])


# =========================================================
# ADMIN: ALL MOVIES
# GET /api/movies/admin/all/
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_all_movies(request):
    permission_error = require_admin(request)
    if permission_error:
        return permission_error

    movies = get_movie_queryset().order_by("-created_at")

    return Response([
        movie_data(request, movie)
        for movie in movies
    ])


# =========================================================
# ADMIN: PENDING MOVIES
# GET /api/movies/admin/pending/
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_pending_movies(request):
    permission_error = require_admin(request)
    if permission_error:
        return permission_error

    movies = (
        get_movie_queryset()
        .filter(status="PENDING")
        .order_by("-created_at")
    )

    return Response([
        movie_data(request, movie)
        for movie in movies
    ])


# =========================================================
# ADMIN: APPROVE OR REJECT
# POST /api/movies/admin/<movie_id>/review/
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_review_movie(request, movie_id):
    permission_error = require_admin(request)
    if permission_error:
        return permission_error

    movie = get_object_or_404(Movie, id=movie_id)

    review_status = request.data.get("status")
    admin_message = request.data.get("admin_message", "")

    if review_status not in ("APPROVED", "REJECTED"):
        return upload_error(
            "Status must be APPROVED or REJECTED."
        )

    movie.status = review_status
    movie.admin_message = str(admin_message).strip()

    # Reviewing a movie does not change its rating.
    movie.save(
        update_fields=[
            "status",
            "admin_message",
            "updated_at",
        ]
    )

    movie = get_movie_queryset().get(pk=movie.pk)

    return Response(
        {
            "message": f"Movie {review_status.lower()}.",
            "movie": movie_data(request, movie),
        },
        status=status.HTTP_200_OK,
    )


# =========================================================
# ADMIN: DELETE MOVIE
# DELETE /api/movies/admin/<movie_id>/delete/
# =========================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def admin_delete_movie(request, movie_id):
    permission_error = require_admin(request)
    if permission_error:
        return permission_error

    movie = get_object_or_404(Movie, id=movie_id)
    movie.delete()

    return Response(
        {"message": "Movie deleted successfully."},
        status=status.HTTP_200_OK,
    )
