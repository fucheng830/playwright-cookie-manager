"""SQLAlchemy backend for cookie storage."""
import json, logging
from datetime import datetime
from typing import Optional
from ..types import CookieAccount

logger = logging.getLogger(__name__)


class SQLBackend:
    """Store cookies in any SQL database via SQLAlchemy. Compatible with wanxiang's platform_accounts table."""

    def __init__(self, database_url: str, table_name: str = "platform_accounts", **kwargs):
        self.database_url = database_url
        self.table_name = table_name
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from sqlalchemy import create_engine
            # Normalize asyncpg URLs to the sync psycopg2 driver
            url = self.database_url.replace("+asyncpg", "+psycopg2")
            self._engine = create_engine(url)
        return self._engine

    def _get_conn(self):
        return self._get_engine().connect()

    def save(self, account: CookieAccount) -> None:
        from sqlalchemy import text
        cookie_json = json.dumps(account.cookie_data.model_dump(), ensure_ascii=False)
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            existing = conn.execute(
                text(f"SELECT id FROM {self.table_name} WHERE platform = :p AND platform_account_id = :aid"),
                {"p": account.platform, "aid": account.account_id}
            ).fetchone()
            if existing:
                conn.execute(
                    text(f"UPDATE {self.table_name} SET cookie_data = :cd, nickname = :n, updated_at = :u WHERE id = :id"),
                    {"cd": cookie_json, "n": account.nickname, "u": now, "id": existing[0]}
                )
            else:
                conn.execute(
                    text(f"INSERT INTO {self.table_name} (id, platform, platform_account_id, nickname, cookie_data, status, created_at, updated_at) VALUES (gen_random_uuid(), :p, :aid, :n, :cd, 1, :now, :now)"),
                    {"p": account.platform, "aid": account.account_id, "n": account.nickname, "cd": cookie_json, "now": now}
                )
            conn.commit()
        logger.info(f"Cookie saved to DB: {account.platform}/{account.account_id}")

    def load(self, platform: str, account_id: str) -> Optional[CookieAccount]:
        from sqlalchemy import text
        with self._get_conn() as conn:
            row = conn.execute(
                text(f"SELECT platform, platform_account_id, nickname, avatar_url, cookie_data FROM {self.table_name} WHERE platform = :p AND platform_account_id = :aid AND cookie_data IS NOT NULL AND status = 1 ORDER BY updated_at DESC LIMIT 1"),
                {"p": platform, "aid": account_id}
            ).fetchone()
        if not row:
            return None
        try:
            cookie_data = json.loads(row[4]) if isinstance(row[4], str) else row[4]
        except (json.JSONDecodeError, TypeError):
            return None
        return CookieAccount(
            platform=row[0], account_id=row[1], nickname=row[2] or "",
            avatar_url=row[3] or "", cookie_data=cookie_data,
        )

    def list(self, platform: str) -> list[str]:
        from sqlalchemy import text
        with self._get_conn() as conn:
            rows = conn.execute(
                text(f"SELECT platform_account_id FROM {self.table_name} WHERE platform = :p AND cookie_data IS NOT NULL AND status = 1"),
                {"p": platform}
            ).fetchall()
        return [r[0] for r in rows]

    def list_platforms(self) -> list[str]:
        """List all platforms that have stored cookies."""
        from sqlalchemy import text
        with self._get_conn() as conn:
            rows = conn.execute(
                text(f"SELECT DISTINCT platform FROM {self.table_name} WHERE cookie_data IS NOT NULL AND status = 1")
            ).fetchall()
        return [r[0] for r in rows]

    def delete(self, platform: str, account_id: str) -> None:
        from sqlalchemy import text
        with self._get_conn() as conn:
            conn.execute(
                text(f"DELETE FROM {self.table_name} WHERE platform = :p AND platform_account_id = :aid"),
                {"p": platform, "aid": account_id}
            )
            conn.commit()
        logger.info(f"Cookie deleted from DB: {platform}/{account_id}")
