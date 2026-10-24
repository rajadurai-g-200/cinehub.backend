
from rest_framework import serializers
from .models import Movie


class MovieUploadSerializer(serializers.ModelSerializer):
    rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        max_value=10,
        required=False,
        default=0.0,
    )

    class Meta:
        model = Movie
        fields = "__all__"
        read_only_fields = (
            "id",
            "status",
            "admin_message",
            "created_at",
            "updated_at",
        )

    def validate_rating(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError(
                "Rating must be between 0.0 and 10.0."
            )
        return value
