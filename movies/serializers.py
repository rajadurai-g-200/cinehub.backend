from rest_framework import serializers

from .models import Movie


class MovieUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie

        fields = [
            "id",
            "title",
            "director",
            "starring",
            "genres",
            "language",
            "release_date",
            "quality",
            "logo",
            "movie_file",
            "status",
        ]

        read_only_fields = [
            "id",
            "status",
        ]

    def create(self, validated_data):
        # Newly uploaded movies await admin approval.
        validated_data["status"] = "PENDING"

        return super().create(validated_data)
