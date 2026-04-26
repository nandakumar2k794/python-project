import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import apps.notifications.routing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()
application = ProtocolTypeRouter({"http": get_asgi_application(), "websocket": AuthMiddlewareStack(URLRouter(apps.notifications.routing.websocket_urlpatterns))})
