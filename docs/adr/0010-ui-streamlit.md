# ADR-0010 — Interface gráfica leve com Streamlit

- Status: Aceito
- Contexto: o feeder era só CLI. Para quem não quer mexer em YAML/linha de
  comando, faltava uma forma visual de ver os dados, disparar um run e ajustar a
  configuração.

## Decisão

Um painel **Streamlit** (`ui/app.py`), como **ferramenta interna** opcional —
Python puro, um comando sobe. Fica num grupo de dependências separado (`ui`)
para **não pesar o core**.

```bash
uv run --group ui streamlit run ui/app.py
```

Três capacidades (o que o usuário pediu):
1. **Dados** — tabela de eventos/notícias do SQLite, com filtros (tipo, UF,
   grupo) e botão **"Rodar agora"** que dispara o pipeline (`flow.do`).
2. **Configuração** — edita **região** (UFs), **grupos** (nome + keywords) e
   **fontes RSS** via `st.data_editor`, e grava no `config.yaml` (limpando o
   cache do `load_config`).
3. Fontes de evento (Even3/Doity/feiras) ficam read-only na UI do v1 — editáveis
   no `config.yaml` (têm campos específicos).

A UI **reusa** o mesmo `initializer()` e `flow` da CLI — é só uma casca. Não há
lógica de negócio nova nela. É excluída do ruff (script de UI) e verificada via
`streamlit.testing.v1.AppTest` (roda o app headless e checa que não lança
exceção).

## Consequências

- ✅ Configurar/ver sem tocar em arquivo nem terminal.
- ✅ Core continua leve: Streamlit só no grupo `ui`.
- ✅ Zero duplicação: a UI chama o mesmo pipeline da CLI.
- ⚠️ Streamlit roda como processo separado (não é a mesma porta do WordPress) —
  é painel de operação interna, não parte pública do site.
- ⚠️ Edição de fontes de evento pela UI fica para o v2 (cada tipo tem campos
  diferentes: categorias no Even3, termos no Doity, datas nas feiras).
