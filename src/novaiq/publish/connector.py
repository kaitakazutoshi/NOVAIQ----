"""Client for the NOVAIQ Connector mu-plugin (custom-header auth).

Works on hosts that strip the standard ``Authorization`` header (e.g. ConoHa
WING) by authenticating with the ``X-NOVAIQ-KEY`` header, which proxies pass
through untouched. Requires ``wordpress/novaiq-connector.php`` installed in
``wp-content/mu-plugins/`` on the site.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import List, Optional

import requests

from ..config import Settings
from .wordpress import WordPressError


class ConnectorClient:
    def __init__(self, settings: Settings):
        if not settings.has_connector:
            raise WordPressError("Connector is not configured (WP_URL / NOVAIQ_API_KEY).")
        self.site = settings.wp_url.rstrip("/")
        self.headers = {"X-NOVAIQ-KEY": settings.novaiq_api_key}

    def _url(self, path: str) -> str:
        # rest_route form avoids WAF path rules on pretty permalinks.
        return f"{self.site}/?rest_route=/novaiq/v1{path}"

    def check_connection(self) -> dict:
        r = requests.get(self._url("/ping"), headers=self.headers, timeout=30)
        if r.status_code >= 400:
            hint = ""
            if r.status_code == 404:
                hint = "（Connectorプラグイン未導入の可能性。mu-plugins に設置してください）"
            elif r.status_code == 401:
                hint = "（NOVAIQ_API_KEY がプラグイン側の値と一致していません）"
            raise WordPressError(f"connector ping -> {r.status_code} {hint}: {r.text[:200]}")
        return r.json()

    def create_draft(
        self,
        *,
        title: str,
        content: str,
        category_names: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
        image_path: Optional[Path] = None,
        slug: str = "",
        status: str = "draft",
    ) -> dict:
        payload: dict = {"title": title, "content": content, "status": status, "slug": slug}
        if category_names:
            payload["categories"] = category_names
        if tag_names:
            payload["tags"] = tag_names
        if image_path and Path(image_path).exists():
            payload["image_base64"] = base64.b64encode(Path(image_path).read_bytes()).decode()
            payload["image_filename"] = Path(image_path).name
        r = requests.post(
            self._url("/post"),
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
        if r.status_code >= 400:
            raise WordPressError(f"connector post -> {r.status_code}: {r.text[:400]}")
        return r.json()
