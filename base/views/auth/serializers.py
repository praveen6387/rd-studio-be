from rest_framework import serializers

from base.models import User, UserPaymentTransaction, UserSocialLinks


class UserPaymentTransactionSerializer(serializers.ModelSerializer):
    transaction_status_name = serializers.CharField(source="get_transaction_status_display", read_only=True)
    transaction_method_name = serializers.CharField(source="get_transaction_method_display", read_only=True)

    class Meta:
        model = UserPaymentTransaction
        fields = "__all__"


class UserSocialLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialLinks
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="get_role_display", read_only=True)
    gender_name = serializers.CharField(source="get_gender_display", read_only=True)
    user_payment_transactions = UserPaymentTransactionSerializer(many=True, read_only=True)
    user_social_links = UserSocialLinksSerializer(many=True, read_only=True)

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
            "remaining_credit",
            "used_credit",
            "user_payment_transactions",
            "user_social_links",
        ]
