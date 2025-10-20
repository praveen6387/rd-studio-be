from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users (role 1 or 3)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get user from the database to check role
        from base.models import User

        try:
            user = User.objects.get(id=request.user.id)
            return user.role in [1, 3]
        except User.DoesNotExist:
            return False


class IsSuperAdminUser(BasePermission):
    """
    Custom permission to only allow super admin users (role 3)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get user from the database to check role
        from base.models import User

        try:
            user = User.objects.get(id=request.user.id)
            return user.role == 3
        except User.DoesNotExist:
            return False


class IsOperationUser(BasePermission):
    """
    Custom permission to only allow operation users (role 2)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get user from the database to check role
        from base.models import User

        try:
            user = User.objects.get(id=request.user.id)
            return user.role == 2
        except User.DoesNotExist:
            return False


class IsAdminOrOperationUser(BasePermission):
    """
    Custom permission to allow admin, super admin, or operation users
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get user from the database to check role
        from base.models import User

        try:
            user = User.objects.get(id=request.user.id)
            return user.role in [1, 2, 3]
        except User.DoesNotExist:
            return False
