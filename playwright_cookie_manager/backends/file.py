"""JSON file backend."""
import json, os, shutil
from datetime import datetime
from typing import Optional
from ..types import CookieAccount


class FileBackend:
    """Store cookies as JSON files: {path}/{platform}/{account_id}.json"""

    def __init__(self, base_path: str):
        self.base_path = base_path

    def _path(self, platform: str, account_id: str) -> str:
        return os.path.join(self.base_path, platform, f"{account_id}.json")

    def save(self, account: CookieAccount) -> None:
        os.makedirs(os.path.dirname(self._path(account.platform, account.account_id)), exist_ok=True)
        tmp = self._path(account.platform, account.account_id) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(account.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        shutil.move(tmp, self._path(account.platform, account.account_id))

    def load(self, platform: str, account_id: str) -> Optional[CookieAccount]:
        p = self._path(platform, account_id)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as f:
            return CookieAccount(**json.load(f))

    def list(self, platform: str) -> list[str]:
        d = os.path.join(self.base_path, platform)
        if not os.path.isdir(d):
            return []
        return [f[:-5] for f in os.listdir(d) if f.endswith(".json")]

    def delete(self, platform: str, account_id: str) -> None:
        p = self._path(platform, account_id)
        if os.path.exists(p):
            os.unlink(p)
