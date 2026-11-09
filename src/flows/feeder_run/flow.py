"""Flow principal do feeder: coleta → classifica → deduplica → persiste → roteia
para os sinks conforme o tipo de conteúdo (ver config.yaml e docs/adr/0006).

v1 é síncrono e disparado por CLI (`python main.py run`). Agendamento (Prefect,
como no oxossi) entra no v2 — ver docs/ROADMAP.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src import App
from src.core.models import Item


@dataclass
class RunReport:
    coletados: int = 0
    classificados: int = 0
    novos: int = 0
    duplicados: int = 0
    publicados: dict[str, int] = field(default_factory=dict)


def _within_region(app: App, item: Item) -> bool:
    aceitas = app.config.regiao.ufs_aceitas
    if not aceitas or item.uf is None:
        return True  # notícia normalmente não tem UF; não filtra por região
    return item.uf in aceitas


def do(app: App | None = None) -> RunReport:
    app = app or _default_app()
    report = RunReport()

    # 1. Coleta de todas as fontes
    raw: list[Item] = []
    for collector in app.collectors:
        raw.extend(collector.collect())
    report.coletados = len(raw)

    # 2. Classificação em funil (keyword -> LLM). Fora do interesse cai aqui.
    classified = app.classifier.classify(raw)
    report.classificados = len(classified)

    # 3. Dedup por mescla (dentro do lote)
    deduped = [i for i in app.dedup.dedupe(classified) if _within_region(app, i)]

    # 4. Persiste + roteia para sinks (idempotente entre execuções)
    for item in deduped:
        if app.storage.exists(item.dedup_key):
            report.duplicados += 1
            continue
        if not app.storage.save(item):
            report.duplicados += 1
            continue
        report.novos += 1
        for sink_name in app.config.sinks_para(item.tipo.value, None):
            sink = app.sinks.get(sink_name)
            if sink is None:
                continue
            sink.publish(item)
            report.publicados[sink_name] = report.publicados.get(sink_name, 0) + 1

    return report


def _default_app() -> App:
    from injector import Injector  # noqa: PLC0415 — evita ciclo de import src<->injector

    return Injector.get_injector()()


if __name__ == "__main__":
    print(do())
