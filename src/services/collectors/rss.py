"""Collector de notícias via RSS/Atom (Trilha A). Funcional no v1.

Usa feedparser: tolera feeds mal-formados e normaliza entradas para `Item`.
Ver docs/adr/0001.
"""

from __future__ import annotations

from datetime import datetime
from time import mktime

import feedparser

from src.core.config import FonteRSS
from src.core.interfaces import ICollector
from src.core.models import ContentType, Item


class RSSCollector(ICollector):
    def __init__(self, fontes: list[FonteRSS]):
        self._fontes = fontes

    def collect(self) -> list[Item]:
        items: list[Item] = []
        for fonte in self._fontes:
            items.extend(self._collect_one(fonte))
        return items

    def _collect_one(self, fonte: FonteRSS) -> list[Item]:
        parsed = feedparser.parse(fonte.url)
        out: list[Item] = []
        for entry in parsed.entries:
            out.append(
                Item(
                    tipo=ContentType.NOTICIA,
                    titulo=getattr(entry, "title", "").strip(),
                    descricao=getattr(entry, "summary", "").strip(),
                    url=getattr(entry, "link", ""),
                    fonte=fonte.id,
                    publicado_em=self._parse_date(entry),
                    # grupos declarados na fonte entram como palpite inicial;
                    # o classifier confirma/ajusta depois.
                    grupos=list(fonte.grupos),
                )
            )
        return out

    @staticmethod
    def _parse_date(entry) -> datetime | None:
        tm = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        return datetime.fromtimestamp(mktime(tm)) if tm else None
