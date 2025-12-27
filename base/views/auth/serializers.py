from rest_framework import serializers

from base.models import User


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="get_role_display", read_only=True)
    gender_name = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_name",
            "phone",
            "gender",
            "gender_name",
            "date_of_birth",
            "organization_name",
            "created_at",
            "is_active",
        ]
