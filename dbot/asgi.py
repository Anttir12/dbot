"""
ASGI config for dbot project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import stt.routing
from dbot.ws_middleware import TokenQueryParameterMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbot.settings')

django_asgi_app = get_asgi_application()
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenQueryParameterMiddleware(
        URLRouter(
                stt.routing.websocket_urlpatterns
        )
    ),
})
