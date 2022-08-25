from urllib import parse
import redis
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import WebsocketDenier
from django.conf import settings



class MultiPathMiddleware:

    def __init__(self, app):
        self.auth_app = AuthMiddlewareStack(app)
        self.token_app = TokenQueryParameterMiddleware(app)

    async def __call__(self, scope, receive, send):
        if scope["path"].startswith("/ws/bot"):
            return await self.token_app(scope, receive, send)
        return await self.auth_app(scope, receive, send)


class TokenQueryParameterMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        r = redis.StrictRedis.from_url(settings.BOT_REDIS_URL, decode_responses=True)
        token = parse.parse_qs(scope['query_string'].decode('utf-8')).get('wsToken', ['-'])[0]

        if r.get(f"ws_token_{token}"):
            return await self.app(scope, receive, send)

        # Deny the connection
        denier = WebsocketDenier()
        return await denier(scope, receive, send)
