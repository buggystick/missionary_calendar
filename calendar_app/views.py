import json
from typing import Dict

from django.db import DatabaseError, IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Signup


def _serialize_signups(signups) -> Dict[str, Dict[str, str]]:
    """Convert signup queryset to the API response structure."""
    return {
        signup.date_key: {
            "name": signup.name,
            "phone": signup.phone,
        }
        for signup in signups
    }


@require_http_methods(["GET", "POST"])
def signup_collection(request: HttpRequest) -> HttpResponse:
    """Handle listing, creating and clearing sign-up records."""
    if request.method == "GET":
        signups = Signup.objects.all()
        return JsonResponse(_serialize_signups(signups))

    raw_body = request.body
    if isinstance(raw_body, (bytes, bytearray)):
        raw_body = raw_body.decode()

    try:
        payload = json.loads(raw_body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    date_key = payload.get("dateKey")
    name = (payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()

    if not date_key:
        return JsonResponse({"error": "dateKey is required"}, status=400)

    try:
        with transaction.atomic():
            try:
                locked_signup = (
                    Signup.objects.select_for_update(nowait=True)
                    .filter(date_key=date_key)
                    .first()
                )
            except DatabaseError:
                return JsonResponse({"message": f"Date {date_key} already taken"})

            if not name and not phone:
                Signup.objects.filter(date_key=date_key).delete()
                return JsonResponse({"message": f"Cleared sign-up for {date_key}"})

            if locked_signup:
                return JsonResponse({"message": f"Date {date_key} already taken"})

            try:
                Signup.objects.create(date_key=date_key, name=name, phone=phone)
            except IntegrityError:
                return JsonResponse({"message": f"Date {date_key} already taken"})

            return JsonResponse({"message": f"Saved sign-up for {date_key}"})
    except DatabaseError:
        return JsonResponse({"error": "Database error"}, status=500)
