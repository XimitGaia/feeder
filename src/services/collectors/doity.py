"""Collector de eventos do Doity (Trilha C — segunda plataforma).

O Doity é um Next.js app sem endpoint JSON público, mas **cada página de evento
expõe um `schema.org/Event` em JSON-LD muito completo** (name, description,
startDate/endDate, location+address, image, organizer, offers). Ver docs/adr/0009.

Fluxo (2 etapas, http puro — sem captcha):
  1. listagem `/eventos?q=<termo>` → coleta as URLs dos cards de evento;
  2. cada URL → lê o JSON-LD Event da página → mapeia para `Item`.

O Doity filtra por TEXTO (não por área), então buscamos pelos `termos` do grupo.
A região (SP) é aplicada depois, no flow, via `uf` (addressRegion).
"""

from __future__ import annotations

import json
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from src.core.config import FonteDoity
from src.core.interfaces import ICollector
from src.core.models import ContentType, Item

_BASE = "https://doity.com.br"
_LISTA = f"{_BASE}/eventos"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; feeder/0.1)"}
_SLUG = re.compile(r"^https://doity\.com\.br/[a-z0-9][a-z0-9-]{4,}$")
_EXCLUI = {"eventos", "area-do-participante"}
_DATA = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:.*?(\d{2}):(\d{2}))?")


class DoityCollector(ICollector):
    def __init__(self, fontes: list[FonteDoity], base_url: str = _BASE):
        self._fontes = fontes
        self._base = base_url.rstrip("/")

    def collect(self) -> list[Item]:
        items: list[Item] = []
        for fonte in self._fontes:
            urls: list[str] = []
            for termo in fonte.termos:
                for url in self._listar(termo):
                    if url not in urls:
                        urls.append(url)
            for url in urls[: fonte.max_eventos]:
                ev = self._ler_evento(url)
                if ev is not None:
                    item = self._to_item(ev, fonte, url)
                    if item is not None:
                        items.append(item)
        return items

    def _listar(self, termo: str) -> list[str]:
        try:
            resp = httpx.get(
                f"{self._base}/eventos", params={"q": termo}, timeout=25.0,
                headers=_HEADERS, follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        urls: list[str] = []
        for a in soup.find_all("a", href=True):
            classes = " ".join(a.get("class", []))
            if "group" not in classes:
                continue
            href = a["href"]
            full = href if href.startswith("http") else f"{self._base}{href}"
            slug = full.rstrip("/").rsplit("/", 1)[-1]
            if _SLUG.match(full) and slug not in _EXCLUI and full not in urls:
                urls.append(full)
        return urls

    def _ler_evento(self, url: str) -> dict | None:
        try:
            resp = httpx.get(url, timeout=25.0, headers=_HEADERS, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for sc in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(sc.string or "{}")
            except (ValueError, TypeError):
                continue
            for obj in data if isinstance(data, list) else [data]:
                if isinstance(obj, dict) and "Event" in str(obj.get("@type", "")):
                    return obj
        return None

    def _to_item(self, ev: dict, fonte: FonteDoity, url: str) -> Item | None:
        titulo = (ev.get("name") or "").strip()
        if not titulo:
            return None
        loc = ev.get("location") or {}
        addr = loc.get("address") or {} if isinstance(loc, dict) else {}
        return Item(
            tipo=ContentType.EVENTO,
            titulo=titulo,
            descricao=(ev.get("description") or "").strip(),
            url=ev.get("url") or url,
            fonte=fonte.id,
            imagem=self._first(ev.get("image")),
            data_inicio=self._parse_date(ev.get("startDate")),
            data_fim=self._parse_date(ev.get("endDate")),
            local=loc.get("name") if isinstance(loc, dict) else None,
            cidade=addr.get("addressLocality") or None,
            uf=addr.get("addressRegion") or None,
            grupos=list(fonte.grupos),
        )

    @staticmethod
    def _first(image) -> str | None:
        if isinstance(image, list):
            return image[0] if image else None
        return image if isinstance(image, str) else None

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        """O Doity emite datas fora do ISO padrão (ex.: '2026-11-18-0314:00').
        Extrai ano/mês/dia (+ hora, se houver) por regex."""
        if not value:
            return None
        m = _DATA.search(value)
        if not m:
            return None
        y, mo, d, hh, mm = m.groups()
        try:
            return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0))
        except ValueError:
            return None
