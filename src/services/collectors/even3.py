"""Collector de eventos do Even3 (Trilha C).

Descoberta: a API pública do Even3 só expõe eventos do dono do token
(ver docs/adr/0004) e o endpoint de busca paginado (`/auxiliar/retornarlistaevento/`)
é protegido por reCAPTCHA v3 + token anti-forgery (ver docs/adr/0007). Mas a home
é alimentada por **JSONs estáticos no Azure Blob**, sem captcha, com dados
estruturados. Consumimos esses blobs e deduplicamos.

Para a maior cobertura possível SEM captcha, combinamos, por categoria:
  - `lista_de_eventos-categoria-{id}.json` → `listaEventosPorCategoriaPaginados`
  - `home-lista_evento.json` → bloco da categoria em `listaEventosPorCategoria`

Categoria `id=1` = "Agricultura, pesca e veterinária" (nosso agro). O filtro de
região (SP) é aplicado depois, no flow, via `siglaEstado`. O catálogo COMPLETO
só está atrás do endpoint com captcha — puxá-lo é trabalho de v2 (Playwright).
"""

from __future__ import annotations

from datetime import datetime

import httpx

from src.core.config import FonteEven3
from src.core.interfaces import ICollector
from src.core.models import ContentType, Item

_BLOB = "https://even3v2.blob.core.windows.net/json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; feeder/0.1)"}


class Even3Collector(ICollector):
    def __init__(self, fontes: list[FonteEven3], blob_base: str = _BLOB):
        self._fontes = fontes
        self._blob = blob_base.rstrip("/")

    def collect(self) -> list[Item]:
        items: list[Item] = []
        for fonte in self._fontes:
            vistos: dict[int, dict] = {}
            for cat in fonte.categorias:
                for ev in self._gather_category(cat):
                    # dedup por id entre os blobs antes de mapear
                    vistos.setdefault(ev.get("id"), ev)
            for ev in vistos.values():
                item = self._to_item(ev, fonte)
                if item is not None:
                    items.append(item)
        return items

    def _gather_category(self, cat: int) -> list[dict]:
        """Eventos de uma categoria vindos dos blobs ungated (combinados)."""
        eventos: list[dict] = []

        por_categoria = self._get_json(f"{self._blob}/lista_de_eventos-categoria-{cat}.json")
        if por_categoria:
            eventos += por_categoria.get("listaEventosPorCategoriaPaginados", [])

        home = self._get_json(f"{self._blob}/home-lista_evento.json")
        if home:
            for bloco in home.get("listaEventosPorCategoria", []):
                if bloco.get("idCategoria") == cat:
                    eventos += bloco.get("eventos", [])

        return eventos

    def _get_json(self, url: str) -> dict | None:
        try:
            resp = httpx.get(url, timeout=25.0, headers=_HEADERS)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError):
            return None

    def _to_item(self, ev: dict, fonte: FonteEven3) -> Item | None:
        if ev.get("passou"):
            return None  # feed de agenda: só eventos futuros
        titulo = (ev.get("titulo") or "").strip()
        url = ev.get("url") or ""
        if not titulo or not url:
            return None
        return Item(
            tipo=ContentType.EVENTO,
            titulo=titulo,
            descricao=(ev.get("resumoEvento") or "").strip(),
            url=url,
            fonte=fonte.id,
            imagem=ev.get("urlImagemBanner") or ev.get("urlImagemInterna"),
            data_inicio=self._parse_date(ev.get("data")),
            data_fim=self._parse_date(ev.get("dataFim")),
            local=ev.get("localRealizacao") or None,
            cidade=ev.get("cidade") or None,
            uf=ev.get("siglaEstado") or None,
            grupos=list(fonte.grupos),
        )

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
