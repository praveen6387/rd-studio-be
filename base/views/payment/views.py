import json
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from base.views.payment.serializers import PaymentGatewaySerializer


class CreatePaymentTransactionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serilzed_data = request.data.copy()
            serilzed_data["user_id"] = request.user.id
            payment_gateway_serializer = PaymentGatewaySerializer(data=serilzed_data, context={"request": request})
            if payment_gateway_serializer.is_valid():
                payment_gateway_serializer.save()
                return Response(
                    {"message": "Payment transaction created successfully"}, status=status.HTTP_201_CREATED
                )
            else:
                return Response({"error": payment_gateway_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
