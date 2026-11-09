# 🌱 Feeder

Agregador de **eventos** e **notícias** sobre agro, plantas e jardinagem.
Coleta de várias fontes, classifica por **grupos de interesse**, deduplica e
entrega para destinos configuráveis (rascunho no WordPress, ou só armazenamento
para consumo por outra via).

> Parte do ecossistema Kaktu/GaiaCorp. Repos são **irmãos** (checkout no mesmo
> diretório-pai) e seguem as convenções do `oxossi`/`witch-doctor`.

## Por que existe

A plataforma tem um app de plantas e um blog que publica eventos. O feeder deixa
os dados **prontos** para: um bloco de "eventos próximos" no WordPress e pautas
de notícia — buscando em várias fontes de forma rápida e automática.

## Como funciona (pipeline)

```
coleta → classifica (funil keyword→LLM) → deduplica → persiste → sinks
```

- **Coleta** — três trilhas (ver [docs/adr/0001](docs/adr/0001-arquitetura-e-trilhas.md)):
  - **A. Notícias via RSS** (funcional) — feedparser sobre portais de agro.
  - **B. Grandes feiras via seed + refresh** — cadastro único + atualização de data.
  - **C. Eventos via scraping** (stub) — as APIs de Sympla/Eventbrite/Even3 só
    expõem os eventos do dono do token, não servem para descoberta.
- **Classifica** — funil: keyword barato primeiro, **Claude Haiku via OpenRouter**
  só no que passa (desambigua grupo, gera tags/resumo). Ver [adr/0002](docs/adr/0002-grupos-de-interesse.md), [adr/0003](docs/adr/0003-di-e-modos.md).
- **Deduplica** — por mescla, mantendo o registro mais rico.
- **Sinks por tipo de conteúdo** — ex.: evento → rascunho no WP; notícia →
  só armazenar. Configurável no `config.yaml`. Ver [adr/0006](docs/adr/0006-sinks-por-tipo.md).

## Rodando

```bash
uv sync
cp .env.example .env     # preencha OpenRouter/WordPress se quiser as etapas 2 e 4
uv run python main.py sources   # lista grupos/fontes/sinks
uv run python main.py run       # executa o pipeline uma vez
```

Sem `OPENROUTER_API_KEY` o feeder roda só com o funil de keyword (sem LLM).
Sem credencial de WordPress, o sink `wordpress_draft` vira no-op. **O v1 roda
sem nenhuma credencial** — só não enriquece nem publica.

## Configuração

- **`config.yaml`** — o QUE buscar/classificar/publicar (grupos, fontes, região,
  sinks). Versionável, sem segredos.
- **`.env`** — segredos e caminhos (tokens, URL do WP, path do banco).

## Estrutura

Ver [docs/MVP.md](docs/MVP.md) para o escopo do marco e as decisões (banco,
interface, estrutura). ADRs em [docs/adr/](docs/adr/).

## Testes / lint

```bash
uv run pytest
uv run ruff check .
```
