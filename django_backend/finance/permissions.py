from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedUser(IsAuthenticated):
    """
    Allows access only to authenticated Django users.
    """
    pass