# 🌱 Feeder

> Agregador de **eventos** e **notícias** sobre **agro, plantas, jardinagem e
> paisagismo** — coleta de várias fontes, classifica por grupos de interesse,
> deduplica e entrega pronto para o WordPress (e outros consumidores).

O Feeder deixa os dados **prontos** para a plataforma: um bloco de "eventos
próximos" no WordPress e pautas de notícia para o blog — buscando em várias
fontes de forma rápida, automática e com curadoria humana no fim.

> Parte do ecossistema Kaktu/GaiaCorp. Repos são **irmãos** (checkout no mesmo
> diretório-pai) e seguem as convenções do `oxossi`/`witch-doctor`.

---

## Índice

- [Como funciona](#como-funciona)
- [Fontes](#fontes)
- [Começando (setup rápido)](#começando-setup-rápido)
- [Interface gráfica](#interface-gráfica)
- [Comandos (CLI)](#comandos-cli)
- [Configuração](#configuração)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Desenvolvimento](#desenvolvimento)
- [Documentação & decisões](#documentação--decisões)
- [Roadmap](#roadmap)

---

## Como funciona

Um **pipeline** disparado por CLI ou pela interface. Cada execução faz o ciclo
completo e termina (é **idempotente** — rodar de novo não duplica):

```
┌─────────────────────┐     a cada execução (main.py run)
│ config.yaml  (o quê)│   ┌──────────────────────────────────────┐
│ .env        (chaves)│──►│ 1. COLETA   RSS · Even3 · Doity · feiras│
└─────────────────────┘   │ 2. CLASSIFICA  keyword → Claude Haiku  │
                          │ 3. DEDUPLICA   por mescla              │
                          │ 4. PERSISTE    SQLite                  │
                          │ 5. ROTEIA      por tipo de conteúdo:   │
                          │    • evento  → rascunho no WordPress   │
                          │    • notícia → só armazena             │
                          └──────────────────────────────────────┘
```

- **Classifica** num **funil**: keyword barato primeiro (peneira grossa, casando
  palavra inteira); **Claude Haiku via OpenRouter** só no que passa — desambigua
  o grupo e gera tags + um resumo curto.
- **Sinks por tipo de conteúdo**: definido no `config.yaml`. Evento vira rascunho
  no WordPress; notícia é só armazenada (consumida de outra forma).
- **Roda sem nenhuma chave** — só não enriquece (sem OpenRouter) nem publica
  (sem WordPress).

## Fontes

**Eventos** (mais de uma plataforma):

| Fonte | Como | Estado |
|---|---|---|
| **Even3** | JSON estruturado por categoria agro (~23 eventos, dedup) | ✅ |
| **Doity** | JSON-LD de cada evento — descrição completa, endereço, foto | ✅ |
| **Grandes feiras** | seed + data da próxima edição (ex. Agrishow 2027) | ✅ |
| Scraper genérico | esqueleto p/ novas fontes (Embrapa/Sympla) | 🟡 stub |

**Notícias** (RSS): Globo Rural, Canal Rural, **Jardineiro.net**, Google News
(queries de agro e de jardinagem/paisagismo).

> As APIs oficiais de Sympla/Eventbrite/Even3 **não** servem para descobrir
> eventos de terceiros — só expõem os eventos do dono do token. Por isso eventos
> vêm de JSON estruturado/JSON-LD e seed. Ver [adr/0004](docs/adr/0004-apis-de-eventos.md).

## Começando (setup rápido)

Pré-requisitos: **Python 3.11+** e **[uv](https://docs.astral.sh/uv/)**.

```bash
uv sync                 # cria o .venv e instala as dependências
cp .env.example .env    # (opcional) preencha as chaves — ver abaixo
uv run python main.py run
uv run python main.py list evento
```

**Chaves de acesso** (todas no `.env`, nunca no `config.yaml`): `OPENROUTER_API_KEY`
(classificação/resumo com Haiku) e `WORDPRESS_URL`/`WORDPRESS_USER`/
`WORDPRESS_APP_PASSWORD` (publicar rascunhos). Onde obter cada uma e o passo a
passo completo: **[docs/CONFIGURACAO.md](docs/CONFIGURACAO.md)**.

## Interface gráfica

Painel **Streamlit** (opcional) para quem não quer CLI/YAML:

```bash
uv run --group ui streamlit run ui/app.py
```

- **📊 Dados** — tabela de eventos/notícias com filtros (tipo, UF, grupo), botão
  **"Rodar agora"** e **sync de eventos para o WordPress** (escolhe eventos,
  categorias e tags → cria rascunho com foto + resumo do Haiku + link oficial).
- **⚙️ Configuração** — informa as **chaves** (grava no `.env`), **puxa
  categorias/tags do WordPress**, e edita **região, grupos e fontes RSS** (grava
  no `config.yaml`).

Ver [adr/0010](docs/adr/0010-ui-streamlit.md) e [adr/0011](docs/adr/0011-sync-wordpress-ui.md).

## Comandos (CLI)

```bash
uv run python main.py run              # executa o pipeline uma vez
uv run python main.py sources          # lista grupos, fontes e sinks
uv run python main.py list evento      # consulta eventos no banco
uv run python main.py list noticia 10  # 10 notícias mais recentes
```

Os dados ficam em **SQLite** (`data/feeder.db`). Dá para consultar pela CLI
acima, pela extensão SQLite do VS Code ou `sqlite3 data/feeder.db`.

### Agendar (rodar sozinho)

No v1 o disparo é manual. Para rodar de hora em hora, use o `cron`:

```cron
0 * * * * cd /caminho/para/feeder && uv run python main.py run >> feeder.log 2>&1
```

Agendamento nativo via Prefect está no [roadmap](docs/ROADMAP.md).

## Configuração

Divisão clara: **segredo** no `.env`; **o quê buscar/classificar/publicar** no
`config.yaml` (versionável):

```yaml
grupos:                      # temas (nome + keywords)
  - nome: agronomia
    keywords: [agronomia, agro, plantio, safra, ...]
regiao:
  ufs_aceitas: [SP]          # v1 começa em SP; expandir = editar a lista
fontes:
  noticias: [...]            # feeds RSS
  feiras_recorrentes: [...]  # grandes feiras (seed + data)
  eventos: [...]             # Even3 (tipo: even3), Doity (tipo: doity)
sinks:
  evento:  [wordpress_draft] # evento → rascunho no WordPress
  noticia: [store_only]      # notícia → só armazena
```

Cadastrar um grupo, fonte ou região nova é **configuração, não código**.

## Estrutura do projeto

```
feeder/
├── config.yaml          # grupos, fontes, região, sinks
├── .env(.example)       # segredos e paths
├── main.py              # CLI (entrypoint)
├── injector.py          # escolhe o modo (prod/test)
├── ui/app.py            # painel Streamlit
├── src/
│   ├── __init__.py          # initializer de produção (composition root)
│   ├── core/                # models, config, env_file, interfaces (I*)
│   ├── services/            # implementações concretas
│   │   ├── collectors/      # rss, even3, doity, feiras, scraper(stub)
│   │   ├── classifier/      # funil keyword → Haiku
│   │   ├── dedup/           # mescla
│   │   ├── storage/         # sqlite
│   │   └── sinks/           # wordpress (sink + client), store_only
│   └── flows/feeder_run/    # orquestração do pipeline
├── tests/               # 18 testes (sem I/O; WP mockado via respx)
├── scripts/docs_check.py    # gate: código exige documentação
└── docs/                    # MVP, ROADMAP, CONFIGURACAO, ADRs
```

## Desenvolvimento

```bash
uv run pytest            # testes (sem rede)
uv run ruff check .      # lint
uv run ruff format .     # formatação
```

Convenções (herdadas de oxossi/witch-doctor): **uv**, src-layout, interfaces
`I*` em `core` e implementações em `services`, modos prod/test via `injector.py`.
O pre-commit roda ruff + um **gate de documentação** (`scripts/docs_check.py`):
mudança de código em `src/` exige um `.md` no mesmo commit. Ver
[CLAUDE.md](CLAUDE.md).

## Documentação & decisões

- **[docs/MVP.md](docs/MVP.md)** — escopo do marco e decisões (banco, interface).
- **[docs/CONFIGURACAO.md](docs/CONFIGURACAO.md)** — setup, chaves, como rodar.
- **[docs/ROADMAP.md](docs/ROADMAP.md)** — pendências e próximos passos.
- **[docs/adr/](docs/adr/)** — Architecture Decision Records (11 decisões).

## Roadmap

Próximos passos (detalhe no [ROADMAP](docs/ROADMAP.md)):

- Refresh automático da data das grandes feiras.
- Geolocalização dos eventos (lat/long para "próximos" de verdade).
- Agendamento via Prefect; API de leitura para o WordPress consumir notícias.
- Mais fontes de evento (Embrapa, Sympla via Playwright) e imagem destacada no WP.
- Migração SQLite → Postgres quando o volume justificar.
