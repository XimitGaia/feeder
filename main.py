"""CLI do feeder (v1).

Comandos:
  python main.py run       — executa o pipeline uma vez (coleta -> ... -> sinks)
  python main.py sources   — lista as fontes/grupos/sinks configurados
"""

from __future__ import annotations

import sys

from injector import Injector
from src.flows.feeder_run import flow


def cmd_run() -> int:
    app = Injector.get_injector()()
    report = flow.do(app)
    print("=== Feeder run ===")
    print(f"coletados     : {report.coletados}")
    print(f"classificados : {report.classificados}")
    print(f"novos         : {report.novos}")
    print(f"duplicados    : {report.duplicados}")
    print(f"publicados    : {report.publicados or '—'}")
    return 0


def cmd_sources() -> int:
    cfg = Injector.get_injector()().config
    print("Grupos de interesse:")
    for g in cfg.grupos:
        print(f"  - {g.nome}: {', '.join(g.keywords[:5])}...")
    print("\nFontes de notícias (RSS):")
    for f in cfg.noticias:
        print(f"  - {f.id} -> grupos {f.grupos}")
    print("\nFeiras recorrentes (seed):")
    for f in cfg.feiras_recorrentes:
        print(f"  - {f.nome} ({f.uf})")
    print("\nFontes de eventos (scraper):")
    for f in cfg.eventos:
        print(f"  - {f.id} [{f.metodo}]")
    print("\nSinks por tipo de conteúdo:")
    for tipo, destinos in cfg.sinks.items():
        print(f"  - {tipo} -> {destinos}")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        return cmd_run()
    if cmd == "sources":
        return cmd_sources()
    print(f"comando desconhecido: {cmd} (use: run | sources)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
