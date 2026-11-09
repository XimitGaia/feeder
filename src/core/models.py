"""Schema único normalizado do feeder.

Tudo que é coletado (notícia de RSS, evento raspado, feira recorrente) é
convertido para `Item` — assim dedup, classificação e sinks trabalham com um
formato só. `tipo` distingue notícia de evento (modelos de dado diferentes:
notícia é fluxo; evento é agenda). Ver docs/adr/0001.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field
from ulid import ULID


class ContentType(StrEnum):
    NOTICIA = "noticia"
    EVENTO = "evento"


class Item(BaseModel):
    """Registro normalizado de um conteúdo coletado."""

    id: str = Field(default_factory=lambda: str(ULID()))
    tipo: ContentType

    titulo: str
    descricao: str = ""
    url: str
    fonte: str
    imagem: str | None = None

    # Campos de agenda (preenchidos só para EVENTO)
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    local: str | None = None
    cidade: str | None = None
    uf: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Preenchidos pela etapa de classificação (LLM/keyword). Ver docs/adr/0002, 0003.
    grupos: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    resumo: str | None = None

    # Chave de deduplicação por mescla (ver docs/adr/0001).
    dedup_key: str | None = None

    publicado_em: datetime | None = None
    coletado_em: datetime = Field(default_factory=lambda: datetime.now(UTC))
