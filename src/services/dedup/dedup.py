"""Deduplicação por mescla (ver docs/adr/0001).

Mesma notícia aparece em vários portais; eventos repetem. A chave de dedup é
derivada do título normalizado (+ URL como fallback). Ao colidir, mantemos o
registro mais RICO (mais campos preenchidos) em vez de descartar.
"""

from __future__ import annotations

import re
import unicodedata

from src.core.interfaces import IDedup
from src.core.models import Item

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = _PUNCT.sub(" ", text.lower())
    return _WS.sub(" ", text).strip()


def dedup_key_for(item: Item) -> str:
    base = _normalize(item.titulo) or item.url
    return f"{item.tipo.value}:{base}"


def _richness(item: Item) -> int:
    return sum(
        1
        for v in (item.descricao, item.imagem, item.data_inicio, item.local, item.resumo)
        if v
    )


class MergeDedup(IDedup):
    def dedupe(self, items: list[Item]) -> list[Item]:
        best: dict[str, Item] = {}
        for item in items:
            key = dedup_key_for(item)
            item.dedup_key = key
            current = best.get(key)
            if current is None or _richness(item) > _richness(current):
                best[key] = item
        return list(best.values())
