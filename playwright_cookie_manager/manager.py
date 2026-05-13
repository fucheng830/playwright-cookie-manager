"""CookieManager — main API."""
import json, logging, os
from datetime import datetime
from typing import Optional
from .types import CookieData, CookieAccount
from .backends.file import FileBackend

logger = logging.getLogger(__name__)

# Environment variable names
ENV_BACKEND = "COOKIE_BACKEND"       # "file" or "sql"
ENV_DB_URL = "COOKIE_DB_URL"        # Database URL for sql backend
ENV_STORAGE_PATH = "COOKIE_PATH"    # File storage path (default: data/cookies)
ENV_DB_TABLE = "COOKIE_DB_TABLE"    # Table name (default: platform_accounts)


class CookieManager:
    """Universal cookie manager with pluggable backends."""

    def __init__(self, conn: str = "", backend: str | object = "", **kwargs):
        # Resolve backend from env if not specified
        if not backend or backend == "":
            backend = os.environ.get(ENV_BACKEND, "file")

        # Resolve connection string from env if not specified
        if not conn or conn == "":
            if backend == "sql":
                conn = os.environ.get(ENV_DB_URL, "")
                if not conn:
                    raise ValueError(f"SQL backend requires {ENV_DB_URL} env var or connection string")
            else:
                conn = os.environ.get(ENV_STORAGE_PATH, "data/cookies")

        if isinstance(backend, str):
            if backend == "file":
                self.backend = FileBackend(conn)
            elif backend == "sql":
                from .backends.sql import SQLBackend
                table = kwargs.pop("table", os.environ.get(ENV_DB_TABLE, "platform_accounts"))
                self.backend = SQLBackend(conn, table_name=table, **kwargs)
            elif backend == "redis":
                from .backends.cloud import RedisBackend
                self.backend = RedisBackend(conn, **kwargs)
            else:
                raise ValueError(f"Unknown backend: {backend}")
        else:
            self.backend = backend

    @classmethod
    def from_env(cls):
        """Create CookieManager from environment variables."""
        return cls()

    def config_info(self) -> dict:
        """Return current configuration info."""
        backend_type = type(self.backend).__name__
        if backend_type == "FileBackend":
            return {"backend": "file", "path": self.backend.base_path}
        elif backend_type == "SQLBackend":
            return {"backend": "sql", "url": self.backend.database_url, "table": self.backend.table_name}
        return {"backend": backend_type}

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
        # List all platforms across all backends
        result = []
        # Prefer backend-native list_platforms() if available
        list_platforms_fn = getattr(self.backend, 'list_platforms', None)
        if list_platforms_fn:
            for plat in list_platforms_fn():
                result.extend(self.list(plat))
            return result
        # Fallback for backends without list_platforms (legacy)
        import os
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
