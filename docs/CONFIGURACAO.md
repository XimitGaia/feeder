# ⚙️ Configuração & Setup

Guia completo para rodar o feeder e saber **onde colocar cada chave de acesso**.

## 1. Pré-requisitos

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (gerenciador de pacotes/venv)

```bash
# instalar o uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Instalar

```bash
uv sync          # cria o .venv e instala tudo a partir do pyproject/uv.lock
```

## 3. Chaves de acesso — onde colocar

**Todas as chaves e segredos vão no arquivo `.env`** (na raiz do projeto).
Nunca no `config.yaml` (esse é versionável e não leva segredo).

```bash
cp .env.example .env     # crie o seu .env a partir do exemplo
```

Depois edite o `.env`. As variáveis:

| Variável | Para quê | Obrigatória? |
|---|---|---|
| `DATABASE_PATH` | caminho do SQLite (padrão `data/feeder.db`) | não |
| `CONFIG_PATH` | caminho do `config.yaml` | não |
| `OPENROUTER_API_KEY` | classificação/descrição via Claude Haiku | só p/ LLM |
| `OPENROUTER_BASE_URL` | endpoint do OpenRouter (já vem preenchido) | não |
| `OPENROUTER_MODEL` | modelo (padrão `anthropic/claude-haiku-4.5`) | não |
| `WORDPRESS_URL` | URL do site WP (ex. `https://seusite.com.br`) | só p/ publicar |
| `WORDPRESS_USER` | usuário do WordPress | só p/ publicar |
| `WORDPRESS_APP_PASSWORD` | Application Password do WP | só p/ publicar |
| `WORDPRESS_DEFAULT_STATUS` | status do post (padrão `draft`) | não |

> **O feeder roda sem nenhuma chave.** Sem `OPENROUTER_API_KEY`, ele degrada
> para classificação só por palavra-chave (sem descrição gerada). Sem as chaves
> do WordPress, o sink `wordpress_draft` vira no-op (não publica).

### 3.1 Chave do OpenRouter (Claude Haiku)

1. Crie conta em <https://openrouter.ai>.
2. Vá em **Keys** → **Create Key**.
3. Cole em `OPENROUTER_API_KEY` no `.env`.
4. (Opcional) Adicione créditos — o Haiku é barato e o feeder usa um funil que
   só chama o LLM no que passa na peneira de keyword (ver
   [adr/0002](adr/0002-grupos-de-interesse.md) e [adr/0003](adr/0003-di-e-modos.md)).

Com isso ligado, cada item ganha **tags** e uma **descrição breve** (`resumo`) —
inclusive para eventos, o que melhora a qualidade do que vai pro WordPress.

### 3.2 Chaves do WordPress (publicar rascunhos)

O feeder usa a **REST API** do WordPress com **Application Password** (não a sua
senha normal):

1. No WordPress, entre em **Usuários → Perfil**.
2. Role até **Senhas de aplicativo** (Application Passwords).
3. Dê um nome (ex. `feeder`) e clique em **Adicionar**.
4. Copie a senha gerada (formato `xxxx xxxx xxxx xxxx`) para
   `WORDPRESS_APP_PASSWORD`, e preencha `WORDPRESS_URL` e `WORDPRESS_USER`.

Os posts são criados como **rascunho** (`draft`) para curadoria humana antes de
publicar (ver [adr/0006](adr/0006-sinks-por-tipo.md)).

## 4. Rodar

```bash
uv run python main.py sources       # mostra grupos, fontes e sinks configurados
uv run python main.py run           # executa o pipeline uma vez
uv run python main.py list evento   # consulta os eventos no banco
uv run python main.py list noticia 10
```

## 4.1 Interface gráfica (painel Streamlit)

Alternativa visual à CLI — ver dados, disparar um run e editar a config sem
mexer em arquivo:

```bash
uv run --group ui streamlit run ui/app.py
```

Abre no navegador (`http://localhost:8501`). Aba **Dados** (tabela + filtros +
"Rodar agora") e aba **Configuração** (região, grupos, fontes RSS → grava no
`config.yaml`). Ver [adr/0010](adr/0010-ui-streamlit.md).

## 5. Consultar os dados

Os dados ficam em **SQLite** (`data/feeder.db`). Formas de ver:

- **CLI**: `uv run python main.py list [evento|noticia] [N]`
- **VS Code**: extensão *SQLite Viewer* → abra `data/feeder.db` → tabela `items`
- **Terminal**: `sqlite3 data/feeder.db "SELECT titulo, fonte FROM items;"`

## 6. Agendar (rodar sozinho)

No v1 o disparo é manual. Para rodar de hora em hora, use o `cron` do sistema:

```cron
0 * * * * cd /caminho/para/feeder && /caminho/uv run python main.py run >> feeder.log 2>&1
```

O agendamento nativo via Prefect (como no `oxossi`) está no
[ROADMAP](ROADMAP.md).

## 7. Config declarativa (`config.yaml`)

O **o quê** buscar/classificar/publicar fica no `config.yaml`:

- `grupos` — temas de interesse (nome + keywords).
- `regiao` — UFs aceitas (v1 começa em `SP`).
- `fontes.noticias` — feeds RSS.
- `fontes.feiras_recorrentes` — grandes feiras (seed + data da próxima edição).
- `fontes.eventos` — fontes de evento (ex. Even3 via `tipo: even3`).
- `sinks` — destino por tipo de conteúdo (`evento → wordpress_draft`,
  `noticia → store_only`).

Detalhes de cada decisão nos [ADRs](adr/).
