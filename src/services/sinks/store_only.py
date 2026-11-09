"""Sink `store_only`: não publica em lugar nenhum — o item só fica no banco,
para ser consumido de outra forma (ex.: notícias que alimentam pautas via uma
consulta direta ao banco/uma API futura). Ver docs/adr/0006.

A persistência em si é feita pelo flow (IStorage); este sink é o "destino nulo"
explícito, para o config poder dizer `noticia: [store_only]`.
"""

from __future__ import annotations

from src.core.interfaces import ISink
from src.core.models import Item


class StoreOnlySink(ISink):
    name = "store_only"

    def publish(self, item: Item) -> None:  # noqa: ARG002 — no-op por design
        return
