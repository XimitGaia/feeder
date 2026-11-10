"""Contratos (`I*`) injetados via witch-doctor. As implementações concretas
vivem em `src/services/`. Qual implementação é bindada depende do modo
(prod/test) escolhido pelo initializer. Ver docs/adr/0003 (DI).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.models import Item


class ICollector(ABC):
    """Coleta itens brutos de uma fonte (RSS, scraper, feira)."""

    @abstractmethod
    def collect(self) -> list[Item]: ...


class IClassifier(ABC):
    """Casa cada item com grupos de interesse e enriquece (tags/resumo).

    Funil: keyword primeiro (barato), LLM depois só no que passou.
    Ver docs/adr/0002 e 0003.
    """

    @abstractmethod
    def classify(self, items: list[Item]) -> list[Item]: ...


class IDedup(ABC):
    """Deduplica por mescla — mantém o registro mais rico. Ver docs/adr/0001."""

    @abstractmethod
    def dedupe(self, items: list[Item]) -> list[Item]: ...


class IStorage(ABC):
    """Persistência dos itens (SQLite no v1)."""

    @abstractmethod
    def save(self, item: Item) -> bool:
        """Retorna True se inseriu, False se já existia (pela dedup_key)."""

    @abstractmethod
    def exists(self, dedup_key: str) -> bool: ...

    @abstractmethod
    def list_recent(self, tipo: str | None = None, limit: int = 20) -> list[Item]:
        """Itens mais recentes (opcionalmente filtrados por tipo) para consulta."""


class ISink(ABC):
    """Destino de saída de um item (WordPress rascunho, store-only, ...)."""

    name: str

    @abstractmethod
    def publish(self, item: Item) -> None: ...
