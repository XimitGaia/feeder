"""Initializer de TESTE: binda stubs sem I/O real (espelha oxossi/tests).

Lê o config de verdade (grupos/sinks), mas troca collectors por fontes fake e
storage por um stub em memória — nada toca rede nem disco.
"""

from __future__ import annotations

from src import App
from src.core.config import load_config
from src.services.classifier.classifier import FunnelClassifier
from src.services.dedup.dedup import MergeDedup
from src.services.sinks.store_only import StoreOnlySink
from tests.mocks import InMemoryStorage, StubCollector, StubSink


def test_initializer() -> App:
    cfg = load_config()
    return App(
        config=cfg,
        collectors=[StubCollector()],
        # api_key vazio => classifier fica só no funil de keyword (sem rede)
        classifier=FunnelClassifier(grupos=cfg.grupos, api_key=""),
        dedup=MergeDedup(),
        storage=InMemoryStorage(),
        sinks={"store_only": StoreOnlySink(), "wordpress_draft": StubSink()},
    )
