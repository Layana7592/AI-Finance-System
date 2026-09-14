from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthenticatedUser(IsAuthenticated):
    """
    Allows access only to authenticated Django users.
    """
    pass


class IsAdmin(BasePermission):
    """
    Allows access only to users with the Admin role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name == "Admin"
        )


class IsManager(BasePermission):
    """
    Allows access only to users with the Manager role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name == "Manager"
        )


class IsAnalyst(BasePermission):
    """
    Allows access only to users with the Analyst role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name == "Analyst"
        )


class IsAdminManagerOrAnalyst(BasePermission):
    """
    Allows access to Admin, Manager, and Analyst users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name in [
                "Admin",
                "Manager",
                "Analyst",
            ]
        )
    

class IsAdminOrManager(BasePermission):
    """
    Allows access to Admin and Manager users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name in ["Admin", "Manager"]
        )


class IsCustomer(BasePermission):
    """ 
    Allows access only to users with the Customer role.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name == "Customer"
        )


class IsAdminManagerOrCustomer(BasePermission):
    """
    Allows access to authenticated Admin, Manager, or Customer users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role.role_name in [
                "Admin",
                "Manager",
                "Customer",
            ]
        )


class IsAdminOrManagerForWrite(IsAuthenticated):
    """
    Allows authenticated users to read.
    Only Admin and Manager can modify data.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return request.user.role.role_name in [
            "Admin",
            "Manager",
        ]


class IsAdminOrManagerForWriteAlerts(IsAuthenticated):
    """
    Authenticated users can read alerts.
    Only Admin and Manager can create, update, or delete alerts.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return request.user.role.role_name in [
            "Admin",
            "Manager",
        ]

