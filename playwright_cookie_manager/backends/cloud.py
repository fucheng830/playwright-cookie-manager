"""Redis cloud backend for distributed cookie storage."""
from __future__ import annotations
import json, logging
from datetime import datetime
from ..types import CookieAccount

logger = logging.getLogger(__name__)

KEY_PREFIX = "cookie-manager"


class RedisBackend:
    """Store cookies in Redis as JSON strings.

    Key format: cookie-manager:{platform}:{account_id}
    """

    def __init__(self, redis_url: str, **kwargs):
        self.redis_url = redis_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            import redis
            self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _key(self, platform: str, account_id: str) -> str:
        return f"{KEY_PREFIX}:{platform}:{account_id}"

    def save(self, account: CookieAccount) -> None:
        client = self._get_client()
        key = self._key(account.platform, account.account_id)
        data = json.dumps(account.model_dump(mode="json"), ensure_ascii=False)
        client.set(key, data)
        logger.info(f"Cookie saved to Redis: {account.platform}/{account.account_id}")

    def load(self, platform: str, account_id: str) -> CookieAccount | None:
        client = self._get_client()
        key = self._key(platform, account_id)
        data = client.get(key)
        if not data:
            return None
        try:
            return CookieAccount(**json.loads(data))
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse cookie data for {key}")
            return None

    def list(self, platform: str) -> list[str]:
        """List account_ids for a given platform."""
        client = self._get_client()
        pattern = f"{KEY_PREFIX}:{platform}:*"
        account_ids = []
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            for k in keys:
                # key format: cookie-manager:{platform}:{account_id}
                parts = k.split(":", 2)
                if len(parts) == 3:
                    account_ids.append(parts[2])
            if cursor == 0:
                break
        return account_ids

    def list_platforms(self) -> list[str]:
        """List all platforms that have stored cookies."""
        client = self._get_client()
        platforms = set()
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=f"{KEY_PREFIX}:*", count=100)
            for k in keys:
                # key format: cookie-manager:{platform}:{account_id}
                parts = k.split(":", 2)
                if len(parts) >= 2:
                    platforms.add(parts[1])
            if cursor == 0:
                break
        return sorted(platforms)

    def delete(self, platform: str, account_id: str) -> None:
        client = self._get_client()
        key = self._key(platform, account_id)
        client.delete(key)
        logger.info(f"Cookie deleted from Redis: {platform}/{account_id}")
