"""Classificação em funil de duas etapas (ver docs/adr/0002 e 0003).

1. Keyword (barato): casa o item com grupos de interesse pelas palavras-chave.
   Item que não bate em nenhum grupo é descartado aqui — custo zero.
2. LLM (Claude Haiku via OpenRouter): só no que passou. Desambigua o grupo,
   gera tags e um resumo curto para pauta. Usar LLM em 100% seria desperdício;
   no funil, o volume que chega nele é pequeno.

Se OPENROUTER_API_KEY não estiver setada, a etapa 2 é pulada (degrada para
só-keyword) — o v1 roda sem credencial, só sem o enriquecimento fino.
"""

from __future__ import annotations

import json
import re

import httpx

from src.core.config import Grupo
from src.core.interfaces import IClassifier
from src.core.models import Item

_SYSTEM = (
    "Você classifica conteúdos (notícias e eventos) sobre agro, plantas e "
    "jardinagem. Responda SEMPRE em JSON: "
    '{"grupos": [str], "tags": [str], "resumo": str}. '
    "grupos deve ser um subconjunto EXATO dos grupos fornecidos. "
    "resumo é uma descrição breve (1 a 2 frases, em português), clara e factual: "
    "para evento, descreve do que se trata e para quem é; para notícia, serve de "
    "pauta de blog. NÃO invente datas, locais ou fatos que não estejam no texto."
)


class FunnelClassifier(IClassifier):
    def __init__(
        self,
        grupos: list[Grupo],
        api_key: str = "",
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "anthropic/claude-haiku-4.5",
    ):
        self._grupos = grupos
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def enrich(self, item: Item) -> Item:
        """Gera resumo/tags de UM item sob demanda (usado pelo botão Sync da UI).
        Sem chave, é no-op. Ver docs/adr/0011."""
        if self._api_key:
            self._enrich_with_llm(item)
        return item

    def classify(self, items: list[Item]) -> list[Item]:
        out: list[Item] = []
        for item in items:
            matched = self._keyword_match(item)
            if not matched:
                continue  # peneira grossa: fora do interesse, descarta
            item.grupos = matched
            if self._api_key:
                self._enrich_with_llm(item)
            out.append(item)
        return out

    # ---- etapa 1: keyword (barato) ----
    def _keyword_match(self, item: Item) -> list[str]:
        haystack = f"{item.titulo} {item.descricao}".lower()
        matched = [
            g.nome
            for g in self._grupos
            if any(self._has_word(k.lower(), haystack) for k in g.keywords)
        ]
        # grupos já sugeridos pela fonte contam como palpite válido
        return sorted(set(matched) | set(item.grupos)) if matched or item.grupos else []

    @staticmethod
    def _has_word(keyword: str, haystack: str) -> bool:
        # palavra inteira: evita "muda" casar em "mudanças", "horta" em "Horta"
        # (cidade) via substring. \b usa fronteira unicode (acentos contam).
        return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None

    # ---- etapa 2: LLM (Haiku via OpenRouter), só no que passou ----
    def _enrich_with_llm(self, item: Item) -> None:
        grupos_nomes = [g.nome for g in self._grupos]
        user = (
            f"Grupos disponíveis: {grupos_nomes}\n"
            f"Título: {item.titulo}\n"
            f"Descrição: {item.descricao[:800]}"
        )
        try:
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": user},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError):
            return  # LLM é enriquecimento; falha nele não derruba o item

        if isinstance(data.get("grupos"), list) and data["grupos"]:
            item.grupos = [g for g in data["grupos"] if g in grupos_nomes] or item.grupos
        if isinstance(data.get("tags"), list):
            item.tags = [str(t) for t in data["tags"]]
        if data.get("resumo"):
            item.resumo = str(data["resumo"])
