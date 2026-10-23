from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):

    display_role = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "role",
            "display_role",
            "is_staff",
            "is_superuser",
        ]

        read_only_fields = [
            "id",
            "email",
            "display_role",
            "is_staff",
            "is_superuser",
        ]

    def get_display_role(self, obj):
        return obj.get_display_role()