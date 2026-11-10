"""Testes do FeirasCollector (Trilha B) — sem I/O, com data de referência fixa."""

from __future__ import annotations

from datetime import date

from src.core.config import FeiraRecorrente
from src.core.models import ContentType
from src.services.collectors.feiras import FeirasCollector

_HOJE = date(2026, 11, 10)

_FEIRAS = [
    FeiraRecorrente(
        id="agrishow",
        nome="Agrishow 2027",
        site_oficial="https://www.agrishow.com.br/",
        cidade="Ribeirão Preto",
        uf="SP",
        data_inicio="2027-04-26",
        data_fim="2027-04-30",
        grupos=["agronomia"],
    ),
    FeiraRecorrente(
        id="passada",
        nome="Feira Passada",
        site_oficial="https://x",
        data_inicio="2026-06-17",  # antes de hoje
    ),
    FeiraRecorrente(
        id="sem_data",
        nome="Hortitec",
        site_oficial="https://www.hortitec.com.br/",
        data_inicio=None,  # ainda sem data: fica fora da agenda
    ),
]


def test_emite_so_feira_futura():
    items = FeirasCollector(_FEIRAS, hoje=_HOJE).collect()
    assert len(items) == 1
    item = items[0]
    assert item.tipo is ContentType.EVENTO
    assert item.titulo == "Agrishow 2027"
    assert item.uf == "SP"
    assert item.data_inicio is not None and item.data_inicio.month == 4
    assert item.url == "https://www.agrishow.com.br/"
