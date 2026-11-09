# CLAUDE.md — guia do repo para agentes

## O que é
Feeder: agrega **eventos** e **notícias** (agro/plantas/jardinagem), classifica
por grupos de interesse, deduplica e entrega a sinks configuráveis. Ver
[README.md](README.md) e [docs/MVP.md](docs/MVP.md).

## Convenções (herdadas de oxossi/witch-doctor)
- **uv** para pacotes (`uv sync`, `uv run ...`). `[tool.uv] package = false`.
- **src-layout**: interfaces `I*` em `src/core/interfaces`, implementações em
  `src/services`, orquestração em `src/flows`.
- **DI por modo**: `injector.py` escolhe prod (`src/__init__.py`) ou test
  (`tests/__init__.py`). Ver [adr/0003](docs/adr/0003-di-e-modos.md).
- **Config vs segredo**: `config.yaml` (o quê, versionável) × `.env` (segredos,
  python-decouple).
- **ruff** + **pre-commit**. `scripts/docs_check.py` **bloqueia commit de código
  sem `.md`** — toda mudança de código em `src/`/entrypoints exige doc no commit
  (exceção consciente: `SKIP=docs-check`).

## Regras de ouro
- Mexeu em código? Atualize/adicione um `.md` no mesmo commit.
- Decisão de arquitetura nova? Novo ADR em `docs/adr/`.
- Nova fonte/grupo/sink? É configuração no `config.yaml`, não código hardcoded.

## Comandos
```bash
uv sync
uv run python main.py sources   # inspeciona config
uv run python main.py run       # roda o pipeline
uv run pytest
uv run ruff check .
```
