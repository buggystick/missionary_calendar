"""ASGI config for config project."""

import os
from importlib import import_module

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

calendar_routing = import_module("calendar.routing")

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(getattr(calendar_routing, "websocket_urlpatterns", []))
    ),
})
