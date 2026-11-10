"""Stubs de teste (sem I/O): collector fake, storage em memória, sink que conta."""

from __future__ import annotations

from src.core.interfaces import ICollector, ISink, IStorage
from src.core.models import ContentType, Item


class StubCollector(ICollector):
    def collect(self) -> list[Item]:
        return [
            Item(
                tipo=ContentType.NOTICIA,
                titulo="Nova técnica de irrigação aumenta a safra",
                descricao="Produtores de agro adotam irrigação por gotejamento.",
                url="https://exemplo.test/n1",
                fonte="stub",
            ),
            Item(
                tipo=ContentType.NOTICIA,
                titulo="Receita de bolo de cenoura",
                descricao="Nada a ver com o tema.",
                url="https://exemplo.test/n2",
                fonte="stub",
            ),
        ]


class InMemoryStorage(IStorage):
    def __init__(self):
        self._keys: set[str] = set()
        self._items: list[Item] = []

    def exists(self, dedup_key: str) -> bool:
        return dedup_key in self._keys

    def save(self, item: Item) -> bool:
        if item.dedup_key in self._keys:
            return False
        self._keys.add(item.dedup_key)
        self._items.append(item)
        return True

    def list_recent(self, tipo: str | None = None, limit: int = 20) -> list[Item]:
        items = [i for i in self._items if tipo is None or i.tipo.value == tipo]
        return items[-limit:][::-1]


class StubSink(ISink):
    name = "stub"

    def __init__(self):
        self.published: list[Item] = []

    def publish(self, item: Item) -> None:
        self.published.append(item)
