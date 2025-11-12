"""calendar_site URL Configuration."""

from __future__ import annotations

from django.contrib import admin
from django.urls import path

from calendar_app import views as calendar_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", calendar_views.calendar_page, name="calendar-page"),
    path("api/signups", calendar_views.signup_collection, name="signup-collection"),
]
