"""Collector das grandes feiras recorrentes (Trilha B).

Padrão seed + refresh (ver docs/adr/0008): as grandes feiras (Agrishow,
Hortitec, ...) são poucas e estáveis, então ficam cadastradas no `config.yaml`
com a data da próxima edição. No v1 a data é semeada à mão (confirmada por
busca); o refresh automático a partir do site oficial é v2.

Só emite feira com `data_inicio` **futura** — o feed é agenda, não histórico.
"""

from __future__ import annotations

from datetime import date, datetime

from src.core.config import FeiraRecorrente
from src.core.interfaces import ICollector
from src.core.models import ContentType, Item


class FeirasCollector(ICollector):
    def __init__(self, feiras: list[FeiraRecorrente], hoje: date | None = None):
        self._feiras = feiras
        self._hoje = hoje or datetime.now().date()

    def collect(self) -> list[Item]:
        items: list[Item] = []
        for feira in self._feiras:
            inicio = self._parse(feira.data_inicio)
            if inicio is None or inicio.date() < self._hoje:
                continue  # sem data ou edição já passou: não entra na agenda
            items.append(
                Item(
                    tipo=ContentType.EVENTO,
                    titulo=feira.nome,
                    descricao=feira.resumo,
                    url=feira.site_oficial,
                    fonte=feira.id,
                    data_inicio=inicio,
                    data_fim=self._parse(feira.data_fim),
                    local=feira.local,
                    cidade=feira.cidade,
                    uf=feira.uf,
                    grupos=list(feira.grupos),
                )
            )
        return items

    @staticmethod
    def _parse(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
