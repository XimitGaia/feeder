# ADR-0011 — Sync de eventos para o WordPress pela UI (chaves, taxonomias, Haiku)

- Status: Aceito
- Contexto: além da publicação automática no pipeline, queríamos um fluxo
  **manual e curado** pela interface: escolher eventos e criar no WordPress com
  qualidade (foto, resumo, link oficial), aplicando categorias/tags do próprio
  WP. E poder informar as chaves sem editar o `.env` à mão.

## Decisão

Três peças novas, todas reaproveitando o que já existe:

1. **Chaves na UI** — a aba Configuração tem campos (password) para OpenRouter e
   WordPress. "Salvar" grava no `.env` via `src/core/env_file.update_env`
   (preserva comentários; atualiza ou acrescenta). A UI usa os valores da
   sessão em runtime (não depende de recarregar o `.env`).

2. **`WordPressClient`** (`services/sinks/wordpress.py`) — puxa
   `GET /wp/v2/categories` e `/tags` do WordPress e cria o post com
   `POST /wp/v2/posts`. O corpo vem de `render_item_html`: para evento, monta
   **foto + ficha (quando/onde) + resumo + link oficial** (sempre). Categorias e
   tags são aplicadas por **id** (escolhidas de uma lista puxada do WP).

3. **Resumo sob demanda com Haiku** — `FunnelClassifier.enrich(item)` gera um
   resumo curto só para o(s) evento(s) escolhido(s), se ainda não houver. Resumo
   **curto e factual** (ADR-0003), não descrição gigante.

Fluxo na UI: aba Dados → expander "Sincronizar eventos" → escolhe eventos,
categorias e tags → "Enviar para WordPress (rascunho)". Cada evento vira um
**draft** para revisão humana.

## Consequências

- ✅ Operação ponta a ponta pela tela: chaves, taxonomias, curadoria e publicação.
- ✅ Qualidade do evento: foto, resumo Haiku e link oficial garantidos.
- ✅ Zero lógica duplicada: render e enrich compartilhados com o pipeline;
  cliente testado com a API mockada (respx).
- ⚠️ Chaves ficam em claro no `.env` (padrão do projeto) — é ambiente local/interno.
- ⚠️ Foto entra **embutida no corpo** (`<img>`); definir imagem destacada
  (featured media, upload em `/wp/v2/media`) fica para o v2.
- ⚠️ Tags são aplicadas por id existente; **criar tag nova** pela UI fica p/ v2.
