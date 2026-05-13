"""CookieManager — main API."""
import json, logging
from datetime import datetime
from typing import Optional
from .types import CookieData, CookieAccount
from .backends.file import FileBackend

logger = logging.getLogger(__name__)


class CookieManager:
    """Universal cookie manager with pluggable backends."""

    def __init__(self, conn: str = "data/cookies", backend: str | object = "file", **kwargs):
        if isinstance(backend, str):
            if backend == "file":
                self.backend = FileBackend(conn)
            elif backend == "sql":
                from .backends.sql import SQLBackend
                table = kwargs.pop("table", "platform_accounts")
                self.backend = SQLBackend(conn, table_name=table, **kwargs)
            elif backend == "redis":
                from .backends.cloud import RedisBackend
                self.backend = RedisBackend(conn, **kwargs)
            else:
                raise ValueError(f"Unknown backend: {backend}")
        else:
            self.backend = backend

    def save(self, platform: str, account_id: str, cookie_data: dict | str,
             nickname: str = "", avatar_url: str = "", metadata: dict | None = None) -> CookieAccount:
        """Save cookie state for a platform account."""
        if isinstance(cookie_data, str):
            cookie_data = json.loads(cookie_data)
        account = CookieAccount(
            platform=platform, account_id=account_id,
            nickname=nickname, avatar_url=avatar_url,
            cookie_data=CookieData(**cookie_data) if isinstance(cookie_data, dict) else cookie_data,
            metadata=metadata or {},
        )
        self.backend.save(account)
        logger.info(f"Cookie saved: {platform}/{account_id}")
        return account

    def load(self, platform: str, account_id: str) -> Optional[dict]:
        """Load Playwright storage_state dict for a platform account."""
        account = self.backend.load(platform, account_id)
        if not account:
            return None
        return account.cookie_data.model_dump()

    def list(self, platform: str | None = None) -> list[dict]:
        """List accounts. Returns [{platform, account_id, nickname}]."""
        if platform:
            ids = self.backend.list(platform)
            result = []
            for aid in ids:
                acc = self.backend.load(platform, aid)
                result.append({"platform": platform, "account_id": aid, "nickname": acc.nickname if acc else ""})
            return result
        # List all platforms
        import os
        result = []
        base = getattr(self.backend, 'base_path', None)
        if base and os.path.isdir(base):
            for plat in os.listdir(base):
                result.extend(self.list(plat))
        return result

    def delete(self, platform: str, account_id: str) -> None:
        """Delete a cookie account."""
        self.backend.delete(platform, account_id)
        logger.info(f"Cookie deleted: {platform}/{account_id}")

    def validate(self, platform: str, account_id: str) -> bool:
        """Check if cookies exist and have auth tokens."""
        data = self.load(platform, account_id)
        if not data:
            return False
        cookies = data.get("cookies", [])
        auth_names = {"auth_token", "web_session", "sessionid", "passport_csrf_token", "csrf", "PHPSESSID"}
        return any(c.get("name") in auth_names for c in cookies)
