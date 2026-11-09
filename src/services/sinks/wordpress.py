"""Sink WordPress: cria o conteúdo como RASCUNHO via REST API (Application
Password). Curadoria humana publica depois — decisão do v1 (ver docs/adr/0006).

Usado tipicamente para EVENTOS. Notícias vão para `store_only` (não publicadas),
porque serão consumidas de outra forma — isso é decidido no config.yaml.
"""

from __future__ import annotations

import httpx

from src.core.interfaces import ISink
from src.core.models import Item


class WordPressDraftSink(ISink):
    name = "wordpress_draft"

    def __init__(self, base_url: str, user: str, app_password: str, status: str = "draft"):
        self._url = base_url.rstrip("/")
        self._auth = (user, app_password)
        self._status = status

    def publish(self, item: Item) -> None:
        if not self._url:
            return  # sem credencial de WP configurada: no-op (v1 roda sem publicar)
        endpoint = f"{self._url}/wp-json/wp/v2/posts"
        body = {
            "title": item.titulo,
            "content": item.resumo or item.descricao,
            "status": self._status,
            "excerpt": item.resumo or "",
        }
        resp = httpx.post(endpoint, json=body, auth=self._auth, timeout=30.0)
        resp.raise_for_status()
