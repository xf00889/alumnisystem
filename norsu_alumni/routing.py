from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
# from messaging.routing import websocket_urlpatterns

# Temporarily disable WebSocket for deployment
# TODO: Implement proper WebSocket routing when needed
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket disabled until proper routing is configured
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(
    #         websocket_urlpatterns
    #     )
    # ),
})