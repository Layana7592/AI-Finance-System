"""Read-only, exploratory one-to-four-month empirical forecast intervals."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.services.forecast_uncertainty import evaluate_uncertainty


class ForecastUncertaintyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = getattr(getattr(request.user, "role", None), "role_name", None)
        if role not in ("Admin", "Analyst"):
            raise PermissionDenied("Global research intervals are for Admin and Analyst only.")
        try:
            months = int(request.query_params.get("months", "12"))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"months": "Must be an integer."}) from exc
        if not 1 <= months <= 24:
            raise ValidationError({"months": "Must be between 1 and 24."})
        result = evaluate_uncertainty(maximum_horizon=months, confidence=0.80)
        return Response(result)
