from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Movie


# =========================================================
# CREATE MOVIE
# =========================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_movie(request):

    user = request.user

    if user.role != "CREATOR":
        return Response(
            {"message": "Only creators can upload movies."},
            status=status.HTTP_403_FORBIDDEN
        )

    title = request.data.get("title")
    release_date = request.data.get("release_date")
    director = request.data.get("director")
    starring = request.data.get("starring")
    genres = request.data.get("genres")
    language = request.data.get("language")
    quality = request.data.get("quality")
    rating = request.data.get("rating", 0)

    logo = request.FILES.get("logo")
    movie_file = request.FILES.get("movie_file")

    if not title:
        return Response(
            {"message": "Movie name is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not release_date:
        return Response(
            {"message": "Release date is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not director:
        return Response(
            {"message": "Director is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not starring:
        return Response(
            {"message": "Starring is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not genres:
        return Response(
            {"message": "Genres are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not language:
        return Response(
            {"message": "Language is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not quality:
        return Response(
            {"message": "Quality is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not logo:
        return Response(
            {"message": "Movie logo is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not movie_file:
        return Response(
            {"message": "Movie file is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    movie = Movie.objects.create(
        creator=user,
        title=title,
        release_date=release_date,
        director=director,
        starring=starring,
        genres=genres,
        language=language,
        quality=quality,
        rating=rating,
        logo=logo,
        movie_file=movie_file,
        status="PENDING"
    )

    return Response(
        {
            "message": "Movie submitted for admin approval.",
            "movie": {
                "id": movie.id,
                "title": movie.title,
                "status": movie.status
            }
        },
        status=status.HTTP_201_CREATED
    )


# =========================================================
# APPROVED MOVIES
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def approved_movies(request):

    movies = Movie.objects.filter(
        status="APPROVED"
    ).order_by("-created_at")

    movie_data = []

    for movie in movies:

        movie_data.append({
            "id": movie.id,
            "title": movie.title,
            "release_date": movie.release_date,
            "director": movie.director,
            "starring": movie.starring,
            "genres": movie.genres,
            "language": movie.language,
            "quality": movie.quality,
            "rating": str(movie.rating),
            "logo": request.build_absolute_uri(
                movie.logo.url
            ) if movie.logo else None,
            "movie_file": request.build_absolute_uri(
                movie.movie_file.url
            ) if movie.movie_file else None,
        })

    return Response(
        movie_data,
        status=status.HTTP_200_OK
    )
    
# =========================================================
# MOVIE DETAILS
# =========================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def movie_details(request, movie_id):

    try:
        movie = Movie.objects.get(
            id=movie_id,
            status="APPROVED"
        )

    except Movie.DoesNotExist:

        return Response(
            {
                "message": "Movie not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            "id": movie.id,
            "title": movie.title,
            "release_date": movie.release_date,
            "director": movie.director,
            "starring": movie.starring,
            "genres": movie.genres,
            "language": movie.language,
            "quality": movie.quality,
            "rating": str(movie.rating),

            "logo": request.build_absolute_uri(
                movie.logo.url
            ) if movie.logo else None,

            "movie_file": request.build_absolute_uri(
                movie.movie_file.url
            ) if movie.movie_file else None,

            "status": movie.status,
        },
        status=status.HTTP_200_OK
    )
    
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import Movie


@api_view(["GET"])
@permission_classes([IsAdminUser])
def pending_movies(request):
    movies = Movie.objects.filter(
        status="PENDING"
    ).select_related("creator").order_by("-created_at")

    data = []

    for movie in movies:
        data.append({
            "id": movie.id,
            "title": movie.title,
            "creator": movie.creator.username,
            "email": movie.creator.email,
            "release_date": movie.release_date,
            "director": movie.director,
            "starring": movie.starring,
            "genres": movie.genres,
            "language": movie.language,
            "quality": movie.quality,
            "rating": str(movie.rating),
            "logo": request.build_absolute_uri(
                movie.logo.url
            ) if movie.logo else None,
            "movie_file": request.build_absolute_uri(
                movie.movie_file.url
            ) if movie.movie_file else None,
            "status": movie.status,
        })

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def review_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response(
            {"message": "Movie not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    action = request.data.get("action")
    admin_message = request.data.get("admin_message", "")

    if action not in ["APPROVED", "REJECTED"]:
        return Response(
            {"message": "Choose APPROVED or REJECTED."},
            status=status.HTTP_400_BAD_REQUEST
        )

    movie.status = action
    movie.admin_message = admin_message
    movie.save(update_fields=["status", "admin_message", "updated_at"])

    return Response({
        "message": f"Movie {action.lower()} successfully.",
        "id": movie.id,
        "status": movie.status,
    })