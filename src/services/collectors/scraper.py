"""Collector de eventos via scraping de páginas de listagem (Trilha C).

STUB no v1: as APIs públicas de Sympla/Eventbrite/Even3 só expõem os eventos
DO DONO do token — não servem para descobrir eventos de terceiros (ver
docs/adr/0004). Por isso a descoberta sai de scraping das listagens.

Escalonamento por fonte (docs/adr/0005):
  - metodo="http": httpx + BeautifulSoup (leve, padrão). Tente sempre primeiro.
  - metodo="playwright": só quando a listagem renderiza via JS. Não implementado
    no v1 — levanta NotImplementedError documentado para plugar depois.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from src.core.config import FonteScraper
from src.core.interfaces import ICollector
from src.core.models import Item


class ScraperCollector(ICollector):
    def __init__(self, fontes: list[FonteScraper]):
        self._fontes = fontes

    def collect(self) -> list[Item]:
        items: list[Item] = []
        for fonte in self._fontes:
            if fonte.metodo == "playwright":
                # Plugar no v2: subir navegador só para esta fonte. Ver docs/adr/0005.
                continue
            items.extend(self._collect_http(fonte))
        return items

    def _collect_http(self, fonte: FonteScraper) -> list[Item]:
        # Esqueleto: baixa o HTML e deixa o parsing por-fonte a implementar.
        # Cada site tem um seletor próprio; isso entra fonte a fonte no v2.
        try:
            resp = httpx.get(fonte.url, timeout=20.0, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError:
            return []
        _soup = BeautifulSoup(resp.text, "html.parser")  # noqa: F841 — parsing por-fonte no v2
        return []
