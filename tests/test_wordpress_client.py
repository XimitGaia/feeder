"""Testes do WordPressClient com a API mockada (respx) — sem WP ao vivo."""

from __future__ import annotations

import json

import httpx
import respx

from src.core.models import ContentType, Item
from src.services.sinks.wordpress import WordPressClient

_ITEM = Item(
    tipo=ContentType.EVENTO,
    titulo="Simpósio de Agronomia",
    descricao="Encontro técnico.",
    url="https://even3.com.br/simposio",
    fonte="even3",
    imagem="https://img/x.jpg",
)


@respx.mock
def test_create_event_posta_corpo_correto():
    route = respx.post("https://wp.test/wp-json/wp/v2/posts").mock(
        return_value=httpx.Response(201, json={"id": 42, "status": "draft"})
    )
    client = WordPressClient("https://wp.test", "user", "app-pass")
    out = client.create_event(_ITEM, categories=[3], tags=[5, 7])

    assert out["id"] == 42
    body = json.loads(route.calls.last.request.content)
    assert body["title"] == "Simpósio de Agronomia"
    assert body["status"] == "draft"
    assert body["categories"] == [3]
    assert body["tags"] == [5, 7]
    assert "Página oficial do evento" in body["content"]  # link oficial sempre
    assert "img/x.jpg" in body["content"]  # foto no corpo


@respx.mock
def test_list_categories_faz_parse():
    respx.get("https://wp.test/wp-json/wp/v2/categories").mock(
        return_value=httpx.Response(
            200, json=[{"id": 1, "name": "Agro", "count": 5}, {"id": 2, "name": "Jardim"}]
        )
    )
    cats = WordPressClient("https://wp.test", "u", "p").list_categories()
    assert cats == [{"id": 1, "name": "Agro"}, {"id": 2, "name": "Jardim"}]


def test_configured_flag():
    assert WordPressClient("https://wp.test", "u", "p").configured
    assert not WordPressClient("", "u", "p").configured
