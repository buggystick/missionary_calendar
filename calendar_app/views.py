from __future__ import annotations

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render


def calendar_page(request: HttpRequest) -> HttpResponse:
    """Render the main calendar page."""
    return render(request, "calendar_app/calendar.html")


def signup_collection(request: HttpRequest) -> JsonResponse:
    """Return a placeholder JSON response for calendar signups."""
    payload = {"signups": []}
    return JsonResponse(payload)
