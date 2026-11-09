# 🎯 Marco — MVP v1 (POC)

Status: **entregue e rodando** · Versão: `0.1.0` · Data: 2026-11-09

## O que é o MVP

Uma POC funcional que prova o pipeline ponta a ponta com dados reais:

> coleta de notícias reais (RSS) → classificação por grupos de interesse →
> deduplicação → persistência (SQLite) → roteamento por sinks (notícia só
> armazena; evento iria para rascunho no WordPress).

Validado: `uv run python main.py run` coletou **151 notícias reais** (RSS) e
**eventos reais de agro em SP** (Even3 — ex.: curso de fertilizantes na
ESALQ-USP, JOIA 2026 na Unesp/Botucatu), persistiu, deduplicou e, numa segunda
execução, reconheceu os itens como duplicados (idempotência). Notícias vão para
`store_only`; eventos são roteados para `wordpress_draft` (rascunho) — a rota
por tipo foi confirmada no run.

## Escopo entregue (v1)

| Peça | Estado | Observação |
|---|---|---|
| **Trilha A — notícias RSS** | ✅ funcional | feedparser sobre portais reais |
| **Funil de classificação** | ✅ funcional | keyword sempre; LLM se houver `OPENROUTER_API_KEY` |
| **Classificação via OpenRouter→Haiku** | ✅ implementada | degrada p/ só-keyword sem credencial |
| **Dedup por mescla** | ✅ funcional | mantém registro mais rico |
| **Persistência SQLite** | ✅ funcional | idempotente via `dedup_key` único |
| **Sinks por tipo de conteúdo** | ✅ funcional | `evento→wordpress_draft`, `noticia→store_only` |
| **Sink WordPress (rascunho)** | ✅ implementado | no-op sem credencial; cria `draft` via REST |
| **CLI** | ✅ `run`, `sources` | interface do v1 |
| **Trilha C — eventos Even3** | ✅ funcional | via JSON estruturado; eventos reais de agro/SP |
| **Trilha B — feiras (seed)** | 🟡 seed cadastrado | refresh de data é v2 |
| **Trilha C — scraper genérico** | 🟡 stub | esqueleto http para outras fontes é v2 |

## Decisões do marco

### Banco de dados → **SQLite**
Zero infra para a POC. Guarda o item serializado (JSON) + `dedup_key` único
(idempotência entre execuções). Migração para Postgres é um ADR futuro quando o
volume/consulta justificar. Ver `src/services/storage/sqlite.py`.

### Interface → **CLI**
`python main.py run | sources`. Sem API/web no v1. O WordPress é **destino**
(sink), não interface. API de leitura para o WP consumir as notícias é v2.

### Estrutura → **src-layout no padrão da casa (oxossi)**
```
feeder/
├── config.yaml          # grupos, fontes, região, sinks (versionável, sem segredo)
├── .env(.example)       # segredos e paths (python-decouple)
├── main.py              # CLI (entrypoint)
├── injector.py          # escolhe o modo (prod/test)
├── src/
│   ├── __init__.py          # initializer de produção (composition root)
│   ├── core/
│   │   ├── models.py        # schema único (Item)
│   │   ├── config.py        # loader de config.yaml + env
│   │   └── interfaces/      # contratos I* (witch-doctor style)
│   ├── services/            # implementações concretas
│   │   ├── collectors/      # rss (ok), scraper (stub)
│   │   ├── classifier/      # funil keyword→Haiku
│   │   ├── dedup/           # mescla
│   │   ├── storage/         # sqlite
│   │   └── sinks/           # wordpress_draft, store_only
│   └── flows/feeder_run/    # orquestração do pipeline
├── tests/                   # stubs sem I/O (modo teste)
├── scripts/docs_check.py    # gate: código exige documentação
└── docs/                    # MVP, ROADMAP, ADRs
```

### Gerenciador → **uv** (`[tool.uv] package = false`), **ruff** + **pre-commit** com docs-check.

## Fora do escopo do v1 (vai para o ROADMAP)

- Refresh automático de datas das feiras (Trilha B).
- Parsing real do scraping de eventos por fonte (Trilha C) e Playwright.
- Geolocalização de eventos ("próximos" de verdade).
- Agendamento via Prefect (hoje é disparo manual por CLI).
- API de leitura para o WordPress consumir notícias (`store_only`).
- Migração SQLite → Postgres.

Ver [ROADMAP.md](ROADMAP.md).
