from django.urls import path

from .views import (
    create_movie,
    approved_movies,
    movie_details,
)

urlpatterns = [
    path(
        "create/",
        create_movie,
        name="create_movie"
    ),

    path(
        "approved/",
        approved_movies,
        name="approved_movies"
    ),

    path(
        "<int:movie_id>/",
        movie_details,
        name="movie_details"
    ),
]