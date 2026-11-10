"""Testes do DoityCollector sem rede (mapeamento do JSON-LD e parse de data)."""

from __future__ import annotations

from src.core.config import FonteDoity
from src.core.models import ContentType
from src.services.collectors.doity import DoityCollector

_LDJSON = {
    "@type": "Event",
    "name": "Simpósio de Agronomia",
    "description": "Encontro técnico sobre produção agrícola.",
    "url": "https://doity.com.br/simposio-agro",
    "startDate": "2026-11-18-0314:00",  # formato fora do ISO padrão do Doity
    "endDate": "2026-11-19-0318:00",
    "image": ["https://img/banner.jpg"],
    "location": {
        "@type": "Place",
        "name": "ESALQ-USP",
        "address": {"addressLocality": "Piracicaba", "addressRegion": "SP"},
    },
}

_FONTE = FonteDoity(id="doity_agro", termos=["agronomia"], grupos=["agronomia"])


def test_parse_date_formato_doity():
    d = DoityCollector._parse_date("2026-11-18-0314:00")
    assert d is not None
    assert (d.year, d.month, d.day, d.hour, d.minute) == (2026, 11, 18, 14, 0)


def test_to_item_mapeia_campos_ricos():
    item = DoityCollector([_FONTE])._to_item(_LDJSON, _FONTE, "https://doity.com.br/x")
    assert item is not None
    assert item.tipo is ContentType.EVENTO
    assert item.titulo == "Simpósio de Agronomia"
    assert item.descricao.startswith("Encontro técnico")
    assert item.cidade == "Piracicaba"
    assert item.uf == "SP"
    assert item.local == "ESALQ-USP"
    assert item.imagem == "https://img/banner.jpg"
    assert item.data_inicio is not None and item.data_inicio.hour == 14
    assert item.grupos == ["agronomia"]


def test_to_item_sem_nome_retorna_none():
    assert DoityCollector([_FONTE])._to_item({"@type": "Event"}, _FONTE, "u") is None
