"""Carregamento da configuração: segredos via `.env` (python-decouple) e o
"o que buscar/publicar" via `config.yaml`. Mesma divisão do oxossi: env guarda
segredo; o restante é declarativo e versionável.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from decouple import config as env
from pydantic import BaseModel


class Grupo(BaseModel):
    nome: str
    descricao: str = ""
    keywords: list[str] = []


class Regiao(BaseModel):
    padrao_uf: str = "SP"
    ufs_aceitas: list[str] = []


class FonteRSS(BaseModel):
    id: str
    tipo: str = "rss"
    url: str
    grupos: list[str] = []
    sinks: list[str] | None = None


class FeiraRecorrente(BaseModel):
    id: str
    nome: str
    site_oficial: str
    local: str | None = None
    uf: str | None = None
    grupos: list[str] = []
    sinks: list[str] | None = None


class FonteScraper(BaseModel):
    id: str
    tipo: str = "scraper"
    metodo: str = "http"  # http | playwright
    url: str
    grupos: list[str] = []
    sinks: list[str] | None = None


class Config(BaseModel):
    grupos: list[Grupo] = []
    regiao: Regiao = Regiao()
    noticias: list[FonteRSS] = []
    feiras_recorrentes: list[FeiraRecorrente] = []
    eventos: list[FonteScraper] = []
    # sinks por tipo de conteúdo: {"evento": [...], "noticia": [...]}
    sinks: dict[str, list[str]] = {}

    def sinks_para(self, tipo: str, override: list[str] | None) -> list[str]:
        """Resolve os destinos de um item: override da fonte vence o padrão do tipo."""
        if override is not None:
            return override
        return self.sinks.get(tipo, [])


@lru_cache
def load_config() -> Config:
    path = Path(env("CONFIG_PATH", default="config.yaml"))
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fontes = raw.pop("fontes", {}) or {}
    return Config(
        grupos=raw.get("grupos", []),
        regiao=raw.get("regiao", {}),
        sinks=raw.get("sinks", {}),
        noticias=fontes.get("noticias", []),
        feiras_recorrentes=fontes.get("feiras_recorrentes", []),
        eventos=fontes.get("eventos", []),
    )
