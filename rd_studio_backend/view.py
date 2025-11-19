from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """
    Public health-check endpoint.

    This view explicitly disables authentication and allows any caller,
    bypassing the global DRF auth/permission configuration.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "OK"})
