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
    cidade: str | None = None
    uf: str | None = None
    # Data da próxima edição (ISO: "2027-04-26"). Semeado à mão no v1; o refresh
    # automático a partir do site oficial é v2. Sem data futura, a feira não é
    # emitida como evento. Ver docs/adr/0008.
    data_inicio: str | None = None
    data_fim: str | None = None
    resumo: str = ""
    grupos: list[str] = []
    sinks: list[str] | None = None


class FonteScraper(BaseModel):
    id: str
    tipo: str = "scraper"
    metodo: str = "http"  # http | playwright
    url: str
    grupos: list[str] = []
    sinks: list[str] | None = None


class FonteEven3(BaseModel):
    id: str
    tipo: str = "even3"
    # ids de categoria do Even3 (1 = "Agricultura, pesca e veterinária").
    categorias: list[int] = []
    grupos: list[str] = []
    sinks: list[str] | None = None


class FonteDoity(BaseModel):
    id: str
    tipo: str = "doity"
    # termos de busca (o Doity filtra por texto, não por área). Ver docs/adr/0009.
    termos: list[str] = []
    max_eventos: int = 20
    grupos: list[str] = []
    sinks: list[str] | None = None


class Config(BaseModel):
    grupos: list[Grupo] = []
    regiao: Regiao = Regiao()
    noticias: list[FonteRSS] = []
    feiras_recorrentes: list[FeiraRecorrente] = []
    eventos_scraper: list[FonteScraper] = []
    eventos_even3: list[FonteEven3] = []
    eventos_doity: list[FonteDoity] = []
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
    eventos = fontes.get("eventos", []) or []
    return Config(
        grupos=raw.get("grupos", []),
        regiao=raw.get("regiao", {}),
        sinks=raw.get("sinks", {}),
        noticias=fontes.get("noticias", []),
        feiras_recorrentes=fontes.get("feiras_recorrentes", []),
        eventos_scraper=[e for e in eventos if e.get("tipo", "scraper") == "scraper"],
        eventos_even3=[e for e in eventos if e.get("tipo") == "even3"],
        eventos_doity=[e for e in eventos if e.get("tipo") == "doity"],
    )
