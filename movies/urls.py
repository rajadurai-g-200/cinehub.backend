from django.urls import path

from .views import (
    AdminMovieUploadView,
    create_movie,
    approved_movies,
    movie_details,
    my_movies,
    admin_all_movies,
    admin_pending_movies,
    admin_review_movie,
    admin_delete_movie,
)

urlpatterns = [
    # Admin movie management
    path(
        "admin/all/",
        admin_all_movies,
        name="admin_all_movies",
    ),
    path(
        "admin/pending/",
        admin_pending_movies,
        name="admin_pending_movies",
    ),
    path(
        "admin/<int:movie_id>/review/",
        admin_review_movie,
        name="admin_review_movie",
    ),
    path(
        "admin/<int:movie_id>/delete/",
        admin_delete_movie,
        name="admin_delete_movie",
    ),
    path(
        "admin/upload/",
        AdminMovieUploadView.as_view(),
        name="admin_movie_upload",
    ),

    # Creator movie management
    path(
        "create/",
        create_movie,
        name="create_movie",
    ),
    path(
        "my/",
        my_movies,
        name="my_movies",
    ),

    # User movie browsing
    path(
        "approved/",
        approved_movies,
        name="approved_movies",
    ),
    path(
        "<int:movie_id>/",
        movie_details,
        name="movie_details",
    ),
]
