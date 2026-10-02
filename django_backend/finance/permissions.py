from rest_framework.permissions import BasePermission, IsAuthenticated


def get_user_role(request):
    """Return the authenticated user's role name safely."""
    user = request.user

    if not user or not user.is_authenticated:
        return None

    role = getattr(user, "role", None)

    if role is None:
        return None

    return role.role_name


class IsAuthenticatedUser(IsAuthenticated):
    """Allow authenticated users only."""
    pass


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) == "Admin"


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) == "Manager"


class IsAnalyst(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) == "Analyst"


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) == "Customer"


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) in ["Admin", "Manager"]


class IsAdminManagerOrAnalyst(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) in [
            "Admin",
            "Manager",
            "Analyst",
        ]


class IsAdminManagerOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request) in [
            "Admin",
            "Manager",
            "Customer",
        ]


class IsAdminOrManagerForWrite(IsAuthenticated):
    """
    Authenticated users can read.
    Only Admin and Manager can modify.
    """

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return get_user_role(request) in ["Admin", "Manager"]


class IsAdminOrManagerForWriteAlerts(IsAdminOrManagerForWrite):
    """
    Authenticated users can read alerts.
    Only Admin and Manager can modify alerts.
    """
    pass