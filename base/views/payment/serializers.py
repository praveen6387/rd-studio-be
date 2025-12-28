from datetime import datetime

from rest_framework import serializers

from base.models import UserPaymentTransaction


class PaymentGatewaySerializer(serializers.Serializer):
    transaction_id = serializers.CharField(required=True)
    transaction_amount = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    user_id = serializers.CharField(required=True, write_only=True)
    transaction_status = serializers.IntegerField(required=False)
    transaction_status_name = serializers.CharField(source="get_transaction_status_display", read_only=True)
    transaction_method_name = serializers.CharField(source="get_transaction_method_display", read_only=True)
    transaction_active_from_date = serializers.DateTimeField(required=False)

    class Meta:
        model = UserPaymentTransaction
        fields = [
            "id",
            "transaction_id",
            "transaction_amount",
            "transaction_status",
            "transaction_status_name",
            "transaction_method",
            "transaction_method_name",
            "remarks",
            "user_id",
            "transaction_active_from_date",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # Map write-only user_id to FK
        user_id = validated_data.pop("user_id")
        return UserPaymentTransaction.objects.create(user_id=user_id, **validated_data)

    def update(self, instance, validated_data):
        # Only allow updating transaction_status (ignore other fields)
        if "transaction_status" in validated_data:
            transaction_status = validated_data["transaction_status"]
            if transaction_status == 1:
                instance.transaction_active_from_date = datetime.now()

            instance.transaction_status = validated_data["transaction_status"]

        instance.save(update_fields=["transaction_status", "updated_at", "transaction_active_from_date"])
        return instance
