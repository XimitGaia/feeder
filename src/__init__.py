"""Initializer de PRODUÇÃO (composition root).

Mesma ideia do oxossi: as interfaces (`I*`) vivem em `src/core/interfaces`; as
implementações concretas em `src/services`; este initializer decide quais são
bindadas e com quais argumentos (lidos de `config.yaml` + `.env`). O modo
(prod/test) é escolhido pelo `Injector` (ver injector.py e docs/adr/0003).

Collectors e sinks são MÚLTIPLOS por natureza, então são expostos como
registries (não um bind 1:1), enquanto classifier/dedup/storage são singulares.
"""

from __future__ import annotations

from decouple import config as env

from src.core.config import Config, load_config
from src.core.interfaces import IClassifier, ICollector, IDedup, ISink, IStorage
from src.services.classifier.classifier import FunnelClassifier
from src.services.collectors.doity import DoityCollector
from src.services.collectors.even3 import Even3Collector
from src.services.collectors.feiras import FeirasCollector
from src.services.collectors.rss import RSSCollector
from src.services.collectors.scraper import ScraperCollector
from src.services.dedup.dedup import MergeDedup
from src.services.sinks.store_only import StoreOnlySink
from src.services.sinks.wordpress import WordPressDraftSink
from src.services.storage.sqlite import SQLiteStorage


class App:
    """Container de dependências já wired — o que o flow consome."""

    def __init__(
        self,
        *,
        config: Config,
        collectors: list[ICollector],
        classifier: IClassifier,
        dedup: IDedup,
        storage: IStorage,
        sinks: dict[str, ISink],
    ):
        self.config = config
        self.collectors = collectors
        self.classifier = classifier
        self.dedup = dedup
        self.storage = storage
        self.sinks = sinks


def initializer() -> App:
    cfg = load_config()

    collectors: list[ICollector] = [
        RSSCollector(cfg.noticias),
        Even3Collector(cfg.eventos_even3),
        DoityCollector(cfg.eventos_doity),
        FeirasCollector(cfg.feiras_recorrentes),
        ScraperCollector(cfg.eventos_scraper),
    ]

    classifier: IClassifier = FunnelClassifier(
        grupos=cfg.grupos,
        api_key=env("OPENROUTER_API_KEY", default=""),
        base_url=env("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"),
        model=env("OPENROUTER_MODEL", default="anthropic/claude-haiku-4.5"),
    )

    storage: IStorage = SQLiteStorage(env("DATABASE_PATH", default="data/feeder.db"))

    sinks: dict[str, ISink] = {
        "store_only": StoreOnlySink(),
        "wordpress_draft": WordPressDraftSink(
            base_url=env("WORDPRESS_URL", default=""),
            user=env("WORDPRESS_USER", default=""),
            app_password=env("WORDPRESS_APP_PASSWORD", default=""),
            status=env("WORDPRESS_DEFAULT_STATUS", default="draft"),
        ),
    }

    return App(
        config=cfg,
        collectors=collectors,
        classifier=classifier,
        dedup=MergeDedup(),
        storage=storage,
        sinks=sinks,
    )
