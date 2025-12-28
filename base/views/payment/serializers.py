from rest_framework import serializers

from base.models import UserPaymentTransaction


class PaymentGatewaySerializer(serializers.Serializer):
    transaction_id = serializers.CharField(required=True)
    transaction_amount = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    user_id = serializers.CharField(required=True)

    class Meta:
        model = UserPaymentTransaction
        fields = [
            "id",
            "transaction_id",
            "transaction_amount",
            "transaction_date",
            "transaction_status",
            "transaction_method",
            "remarks",
        ]

    def create(self, validated_data):
        return UserPaymentTransaction.objects.create(**validated_data)
