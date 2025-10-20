import json
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from base.models import User


# JWT Token utilities
def generate_jwt_token(user):
    """Generate JWT token for user using SimpleJWT"""
    refresh = RefreshToken.for_user(user)

    # Add custom claims to the access token
    refresh["email"] = user.email
    refresh["role"] = user.role
    refresh["is_admin"] = user.role in [1, 3]  # admin or super admin
    refresh["is_super_admin"] = user.role == 3

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def decode_jwt_token(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(token):
    """Get user from JWT token"""
    payload = decode_jwt_token(token)
    if payload:
        try:
            user = User.objects.get(id=payload["user_id"])
            return user
        except User.DoesNotExist:
            return None
    return None


class LoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "Login endpoint"})

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not all([email, password]):
            return Response({"error": "Email, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.password == password:  # In production, use proper password hashing
                # Generate JWT token
                tokens = generate_jwt_token(user)

                return Response(
                    {
                        "message": "Login successful",
                        "access": tokens["access"],
                        "refresh": tokens["refresh"],
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "role": user.role,
                            "role_name": user.get_role_display(),
                            "phone": user.phone,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class UserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        users = User.objects.all()
        user_list = []
        for user in users:
            user_list.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "phone": user.phone,
                    "gender": user.gender,
                    "date_of_birth": user.date_of_birth,
                    "created_at": user.created_at,
                    "is_active": user.is_active,
                }
            )
        return Response(
            {"message": "Users retrieved successfully", "count": len(user_list), "users": user_list},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        try:
            # Validate required fields
            required_fields = ["email", "password", "phone", "first_name", "last_name"]
            for field in required_fields:
                if not request.data.get(field):
                    return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user already exists
            if User.objects.filter(email=request.data.get("email")).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(phone=request.data.get("phone")).exists():
                return Response(
                    {"error": "User with this phone number already exists"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Create user
            user = User.objects.create(
                username=request.data.get("email"),  # Use email as username
                email=request.data.get("email"),
                password=request.data.get("password"),  # In production, hash this
                phone=request.data.get("phone"),
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                role=request.data.get("role", 0),  # Default to customer
                gender=request.data.get("gender"),
                date_of_birth=request.data.get("date_of_birth"),
            )

            return Response(
                {
                    "message": "User created successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "phone": user.phone,
                        "gender": user.gender,
                        "date_of_birth": user.date_of_birth,
                        "created_at": user.created_at,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to create user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        user_id = request.data.get("id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)

            # Update fields if provided
            if request.data.get("email"):
                user.email = request.data.get("email")
            if request.data.get("password"):
                user.password = request.data.get("password")
            if request.data.get("phone"):
                user.phone = request.data.get("phone")
            if request.data.get("first_name"):
                user.first_name = request.data.get("first_name")
            if request.data.get("last_name"):
                user.last_name = request.data.get("last_name")
            if request.data.get("role") is not None:
                user.role = request.data.get("role")
            if request.data.get("gender") is not None:
                user.gender = request.data.get("gender")
            if request.data.get("date_of_birth"):
                user.date_of_birth = request.data.get("date_of_birth")

            user.save()

            return Response(
                {
                    "message": "User updated successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                        "phone": user.phone,
                        "gender": user.gender,
                        "date_of_birth": user.date_of_birth,
                        "updated_at": user.updated_at,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"Failed to update user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        user_id = request.data.get("id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"Failed to delete user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
