"""Integração com o WordPress (REST API + Application Password).

Dois usos:
- `WordPressDraftSink`: sink do pipeline (cria rascunho automaticamente).
- `WordPressClient`: usado pela UI para o botão "Sync" — puxa categorias/tags do
  WP e cria o post do evento com título, foto, resumo e link oficial.

Ambos compartilham `render_item_html`. Para EVENTO monta uma ficha (foto, quando,
onde, resumo curto) e **sempre** o link oficial. Ver docs/adr/0006 e 0011.
"""

from __future__ import annotations

import httpx

from src.core.interfaces import ISink
from src.core.models import ContentType, Item


def render_item_html(item: Item) -> str:
    """Corpo do post. Notícia: texto simples. Evento: ficha com foto + link."""
    if item.tipo is not ContentType.EVENTO:
        return item.resumo or item.descricao

    partes: list[str] = []
    if item.imagem:
        partes.append(f'<p><img src="{item.imagem}" alt="{item.titulo}" /></p>')

    ficha: list[str] = []
    if item.data_inicio:
        quando = item.data_inicio.date().isoformat()
        if item.data_fim:
            quando += f" a {item.data_fim.date().isoformat()}"
        ficha.append(f"<strong>Quando:</strong> {quando}")
    onde = ", ".join(p for p in (item.local, item.cidade, item.uf) if p)
    if onde:
        ficha.append(f"<strong>Onde:</strong> {onde}")
    if ficha:
        partes.append("<p>" + "<br>".join(ficha) + "</p>")

    corpo = item.resumo or item.descricao
    if corpo:
        partes.append(f"<p>{corpo}</p>")
    if item.url:
        partes.append(
            f'<p><a href="{item.url}" target="_blank" rel="noopener">'
            "Página oficial do evento</a></p>"
        )
    return "\n".join(partes)


def _excerpt(item: Item) -> str:
    return item.resumo or item.descricao[:160]


class WordPressDraftSink(ISink):
    name = "wordpress_draft"

    def __init__(self, base_url: str, user: str, app_password: str, status: str = "draft"):
        self._url = base_url.rstrip("/")
        self._auth = (user, app_password)
        self._status = status

    def publish(self, item: Item) -> None:
        if not self._url:
            return  # sem credencial: no-op (o pipeline roda sem publicar)
        body = {
            "title": item.titulo,
            "content": render_item_html(item),
            "status": self._status,
            "excerpt": _excerpt(item),
        }
        resp = httpx.post(
            f"{self._url}/wp-json/wp/v2/posts", json=body, auth=self._auth, timeout=30.0
        )
        resp.raise_for_status()


class WordPressClient:
    """Cliente para a UI: puxa taxonomias do WP e cria o post do evento."""

    def __init__(self, base_url: str, user: str, app_password: str, status: str = "draft"):
        self._url = base_url.rstrip("/")
        self._auth = (user, app_password)
        self._status = status

    @property
    def configured(self) -> bool:
        return bool(self._url and self._auth[0] and self._auth[1])

    def list_categories(self) -> list[dict]:
        return self._taxonomy("categories")

    def list_tags(self) -> list[dict]:
        return self._taxonomy("tags")

    def _taxonomy(self, kind: str) -> list[dict]:
        resp = httpx.get(
            f"{self._url}/wp-json/wp/v2/{kind}",
            params={"per_page": 100, "hide_empty": False},
            auth=self._auth,
            timeout=30.0,
        )
        resp.raise_for_status()
        return [{"id": t["id"], "name": t["name"]} for t in resp.json()]

    def create_event(
        self, item: Item, categories: list[int] | None = None, tags: list[int] | None = None
    ) -> dict:
        body: dict = {
            "title": item.titulo,
            "content": render_item_html(item),
            "status": self._status,
            "excerpt": _excerpt(item),
        }
        if categories:
            body["categories"] = categories
        if tags:
            body["tags"] = tags
        resp = httpx.post(
            f"{self._url}/wp-json/wp/v2/posts", json=body, auth=self._auth, timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()
