import json
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.models import UserPaymentTransaction
from base.views.payment.serializers import PaymentGatewaySerializer


class PaymentTransactionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serilzed_data = request.data.copy()

            if "user_id" not in serilzed_data:
                serilzed_data["user_id"] = request.user.id

            payment_gateway_serializer = PaymentGatewaySerializer(data=serilzed_data)
            if payment_gateway_serializer.is_valid():
                try:
                    payment_gateway_serializer.save()
                    return Response(
                        {
                            "message": "Payment transaction created successfully",
                            "data": payment_gateway_serializer.data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                except IntegrityError as e:
                    error_message = "A transaction with this transaction_id already exists."
                    return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": payment_gateway_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, payment_id):
        try:
            current_user = request.user
            if current_user.role not in [3, 4]:
                return Response(
                    {"error": "You are not authorized to access this endpoint"}, status=status.HTTP_403_FORBIDDEN
                )

            payment_gateway_instance = UserPaymentTransaction.objects.get(id=payment_id)

            if payment_gateway_instance.transaction_status in [1, 2]:
                return Response(
                    {"error": "Payment transaction can't be updated more"}, status=status.HTTP_400_BAD_REQUEST
                )

            serilzed_data = request.data.copy()
            payment_gateway_serializer = PaymentGatewaySerializer(
                instance=payment_gateway_instance, data=serilzed_data, partial=True
            )
            if payment_gateway_serializer.is_valid():
                payment_gateway_serializer.save()
                return Response(
                    {
                        "message": "Payment transaction updated successfully",
                        "data": payment_gateway_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
        except UserPaymentTransaction.DoesNotExist:
            return Response({"error": "Payment transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
