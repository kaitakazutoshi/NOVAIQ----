"""Minimal WordPress REST API client (Application Password auth).

ConoHa / Apache notes:
- Some ConoHa sites have a WAF rule that returns a 403 (Apache HTML page) for
  authenticated requests to the pretty ``/wp-json/...`` path. To be robust we try
  the official ``?rest_route=/wp/v2/...`` endpoint form first (which typically
  bypasses that path rule) and fall back to the pretty path.
- If the ``Authorization`` header is stripped by the server before it reaches
  PHP, WordPress returns ``rest_not_logged_in``. That must be fixed server-side
  (see README / setup notes) by forwarding the Authorization header.
"""
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
        self.site = settings.wp_url.rstrip("/")
        self.auth = HTTPBasicAuth(settings.wp_username, settings.wp_app_password)

    def _endpoints(self, path: str) -> List[str]:
        # rest_route form first (bypasses ConoHa WAF path rules), then pretty path.
        return [
            f"{self.site}/?rest_route=/wp/v2{path}",
            f"{self.site}/wp-json/wp/v2{path}",
        ]

    def _request(self, method: str, path: str, **kw) -> requests.Response:
        last: Optional[requests.Response] = None
        for url in self._endpoints(path):
            resp = requests.request(method, url, auth=self.auth, timeout=90, **kw)
            last = resp
            ctype = resp.headers.get("content-type", "")
            # Accept success, or any JSON response (real WP error we can surface).
            if resp.status_code < 400 or "application/json" in ctype:
                return resp
            # Otherwise (e.g. WAF HTML 403) try the next endpoint form.
        assert last is not None
        return last

    def _json(self, method: str, path: str, **kw) -> dict:
        resp = self._request(method, path, **kw)
        if resp.status_code >= 400:
            raise WordPressError(f"{method} {path} -> {resp.status_code}: {resp.text[:400]}")
        return resp.json()

    def check_connection(self) -> dict:
        resp = self._request("GET", "/users/me")
        if resp.status_code >= 400:
            hint = ""
            if "rest_not_logged_in" in resp.text:
                hint = (
                    "（Authorizationヘッダがサーバでカットされています。"
                    ".htaccessでの転送設定が必要です）"
                )
            elif resp.status_code == 403 and "<html" in resp.text.lower():
                hint = "（サーバのWAF/403ルールにブロックされています）"
            raise WordPressError(f"接続確認に失敗: {resp.status_code} {hint}")
        return resp.json()

    def ensure_term(self, taxonomy: str, name: str) -> int:
        found = self._json("GET", f"/{taxonomy}", params={"search": name, "per_page": 100})
        for term in found:
            if term.get("name") == name:
                return term["id"]
        created = self._json("POST", f"/{taxonomy}", json={"name": name})
        return created["id"]

    def upload_media(self, image_path: Path, title: str = "eyecatch") -> int:
        mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
        data = Path(image_path).read_bytes()
        headers = {
            "Content-Disposition": f'attachment; filename="{Path(image_path).name}"',
            "Content-Type": mime,
        }
        resp = self._request("POST", "/media", headers=headers, data=data)
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
        return self._json("POST", "/posts", json=payload)
