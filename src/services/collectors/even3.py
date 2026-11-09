"""Collector de eventos do Even3 (Trilha C).

Descoberta: a API pública do Even3 só expõe os eventos do dono do token
(ver docs/adr/0004). Mas a home do site é alimentada por um JSON estático e
estruturado no Azure Blob — `home-lista_evento.json` — com eventos agrupados por
categoria e campos ricos (datas, cidade, UF, local, resumo, imagem). Consumir
esse JSON é limpo e estável: não é raspar template HTML AngularJS.

A categoria `id=1` é "Agricultura, pesca e veterinária" — o nosso agro. O filtro
de região (SP) é aplicado depois, no flow, via `siglaEstado`.
"""

from __future__ import annotations

from datetime import datetime

import httpx

from src.core.config import FonteEven3
from src.core.interfaces import ICollector
from src.core.models import ContentType, Item

_FEED_URL = "https://even3v2.blob.core.windows.net/json/home-lista_evento.json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; feeder/0.1)"}


class Even3Collector(ICollector):
    def __init__(self, fontes: list[FonteEven3], feed_url: str = _FEED_URL):
        self._fontes = fontes
        self._feed_url = feed_url

    def collect(self) -> list[Item]:
        if not self._fontes:
            return []
        blocos = self._fetch_blocos()
        if not blocos:
            return []

        items: list[Item] = []
        for fonte in self._fontes:
            categorias = set(fonte.categorias)
            for bloco in blocos:
                if categorias and bloco.get("idCategoria") not in categorias:
                    continue
                for ev in bloco.get("eventos", []):
                    item = self._to_item(ev, fonte)
                    if item is not None:
                        items.append(item)
        return items

    def _fetch_blocos(self) -> list[dict]:
        try:
            resp = httpx.get(self._feed_url, timeout=25.0, headers=_HEADERS)
            resp.raise_for_status()
            return resp.json().get("listaEventosPorCategoria", [])
        except (httpx.HTTPError, ValueError):
            return []

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
