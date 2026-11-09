"""Testes do Even3Collector sem rede (blocos injetados via monkeypatch)."""

from __future__ import annotations

from src.core.config import FonteEven3
from src.core.models import ContentType
from src.services.collectors.even3 import Even3Collector

_BLOCOS = [
    {
        "idCategoria": 1,  # agro
        "eventos": [
            {
                "titulo": "Curso de Fertilizantes",
                "url": "https://even3.com.br/curso-123",
                "resumoEvento": "Controle de qualidade.",
                "data": "2026-11-12T00:00:00",
                "dataFim": "2026-11-13T00:00:00",
                "cidade": "Piracicaba",
                "siglaEstado": "SP",
                "localRealizacao": "ESALQ-USP",
                "urlImagemBanner": "https://img/x.jpg",
                "passou": False,
            },
            {"titulo": "Evento passado", "url": "u", "passou": True},  # deve sair
            {"titulo": "", "url": "u2", "passou": False},  # sem título: sai
        ],
    },
    {
        "idCategoria": 99,  # outra categoria: ignorada pelo filtro
        "eventos": [{"titulo": "Fora", "url": "u3", "passou": False}],
    },
]


def _collector() -> Even3Collector:
    col = Even3Collector([FonteEven3(id="even3_agro", categorias=[1], grupos=["agronomia"])])
    col._fetch_blocos = lambda: _BLOCOS  # type: ignore[method-assign]
    return col


def test_filtra_categoria_e_passados():
    items = _collector().collect()
    assert len(items) == 1  # só o curso válido da categoria 1


def test_mapeia_campos_do_evento():
    item = _collector().collect()[0]
    assert item.tipo is ContentType.EVENTO
    assert item.titulo == "Curso de Fertilizantes"
    assert item.cidade == "Piracicaba"
    assert item.uf == "SP"
    assert item.local == "ESALQ-USP"
    assert item.data_inicio is not None and item.data_inicio.year == 2026
    assert item.imagem == "https://img/x.jpg"
    assert item.grupos == ["agronomia"]
