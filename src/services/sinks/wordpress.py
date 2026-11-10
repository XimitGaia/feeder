"""Sink WordPress: cria o conteúdo como RASCUNHO via REST API (Application
Password). Curadoria humana publica depois — decisão do v1 (ver docs/adr/0006).

Usado tipicamente para EVENTOS. Notícias vão para `store_only` (não publicadas),
porque serão consumidas de outra forma — isso é decidido no config.yaml.
"""

from __future__ import annotations

import httpx

from src.core.interfaces import ISink
from src.core.models import ContentType, Item


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
            "content": self._render_content(item),
            "status": self._status,
            "excerpt": item.resumo or item.descricao[:160],
        }
        resp = httpx.post(endpoint, json=body, auth=self._auth, timeout=30.0)
        resp.raise_for_status()

    @staticmethod
    def _render_content(item: Item) -> str:
        """Corpo do rascunho. Para eventos, monta uma ficha (data, local, link)
        além da descrição — qualidade do evento. Ver docs/adr/0006."""
        descricao = item.resumo or item.descricao
        if item.tipo is not ContentType.EVENTO:
            return descricao

        linhas: list[str] = []
        if item.data_inicio:
            quando = item.data_inicio.date().isoformat()
            if item.data_fim:
                quando += f" a {item.data_fim.date().isoformat()}"
            linhas.append(f"<strong>Quando:</strong> {quando}")
        onde = ", ".join(p for p in (item.local, item.cidade, item.uf) if p)
        if onde:
            linhas.append(f"<strong>Onde:</strong> {onde}")
        ficha = "<br>".join(linhas)
        link = f'<p><a href="{item.url}">Mais informações</a></p>' if item.url else ""
        corpo = f"<p>{descricao}</p>" if descricao else ""
        return f"{ficha}{corpo}{link}".strip()
