"""Minimal WordPress REST API client (Application Password auth)."""
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import List, Optional

import requests
from requests.auth import HTTPBasicAuth

from ..config import Settings


class WordPressError(RuntimeError):
    pass


class WordPressClient:
    def __init__(self, settings: Settings):
        if not settings.has_wordpress:
            raise WordPressError("WordPress credentials are not configured.")
        self.base = settings.wp_url.rstrip("/") + "/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(settings.wp_username, settings.wp_app_password)

    def _req(self, method: str, path: str, **kw) -> dict:
        url = f"{self.base}{path}"
        resp = requests.request(method, url, auth=self.auth, timeout=60, **kw)
        if resp.status_code >= 400:
            raise WordPressError(f"{method} {path} -> {resp.status_code}: {resp.text[:400]}")
        return resp.json()

    def check_connection(self) -> dict:
        """Verify auth by fetching the current user."""
        url = self.base.replace("/wp/v2", "/wp/v2") + "/users/me"
        resp = requests.get(url, auth=self.auth, timeout=30)
        if resp.status_code >= 400:
            raise WordPressError(f"接続確認に失敗: {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def ensure_term(self, taxonomy: str, name: str) -> int:
        """Return the id of a category/tag by name, creating it if needed."""
        path = f"/{taxonomy}"
        found = self._req("GET", path, params={"search": name, "per_page": 100})
        for term in found:
            if term.get("name") == name:
                return term["id"]
        created = self._req("POST", path, json={"name": name})
        return created["id"]

    def upload_media(self, image_path: Path, title: str = "eyecatch") -> int:
        mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
        data = Path(image_path).read_bytes()
        headers = {
            "Content-Disposition": f'attachment; filename="{Path(image_path).name}"',
            "Content-Type": mime,
        }
        resp = requests.post(
            f"{self.base}/media", auth=self.auth, headers=headers, data=data, timeout=120
        )
        if resp.status_code >= 400:
            raise WordPressError(f"media upload -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()["id"]

    def create_draft(
        self,
        *,
        title: str,
        content: str,
        category_names: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
        featured_media: Optional[int] = None,
        slug: str = "",
        status: str = "draft",
    ) -> dict:
        payload: dict = {"title": title, "content": content, "status": status}
        if slug:
            payload["slug"] = slug
        if category_names:
            payload["categories"] = [self.ensure_term("categories", n) for n in category_names]
        if tag_names:
            payload["tags"] = [self.ensure_term("tags", n) for n in tag_names]
        if featured_media:
            payload["featured_media"] = featured_media
        return self._req("POST", "/posts", json=payload)
