import redis
from channels.security.websocket import WebsocketDenier
from django.conf import settings
from urllib import parse


class TokenQueryParameterMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        r = redis.StrictRedis.from_url(settings.BOT_REDIS_URL, decode_responses=True)
        token = parse.parse_qs(scope['query_string'].decode('utf-8')).get('wsToken', ['-'])[0]

        if r.get(f"ws_token_{token}"):
            return await self.app(scope, receive, send)
        else:
            # Deny the connection
            denier = WebsocketDenier()
            return await denier(scope, receive, send)


