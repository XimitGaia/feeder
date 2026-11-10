"""Painel do feeder (Streamlit) — ferramenta interna leve.

Capacidades (ver docs/adr/0010 e 0011):
  1. Ver os dados coletados (eventos/notícias) com filtros;
  2. Disparar o pipeline ("Rodar agora");
  3. Editar a configuração (grupos, região, fontes RSS) → grava no config.yaml;
  4. Guardar as chaves (OpenRouter/WordPress) → grava no .env;
  5. Sincronizar eventos para o WordPress (rascunho com foto, resumo Haiku e
     link oficial), aplicando categorias/tags puxadas do próprio WordPress.

Rodar:  uv run --group ui streamlit run ui/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# `streamlit run ui/app.py` coloca ui/ no sys.path e pode herdar outro cwd.
# Fixamos a raiz no path E como cwd para import src / config.yaml / data/ resolverem.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import streamlit as st
import yaml
from decouple import config as env

from src import initializer
from src.core.config import load_config
from src.core.env_file import update_env
from src.flows.feeder_run import flow
from src.services.classifier.classifier import FunnelClassifier
from src.services.sinks.wordpress import WordPressClient

CONFIG_PATH = ROOT / env("CONFIG_PATH", default="config.yaml")
ENV_PATH = ROOT / ".env"
BR_UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


def load_raw() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def save_raw(data: dict) -> None:
    CONFIG_PATH.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    load_config.cache_clear()


def build_app():
    load_config.cache_clear()
    return initializer()


def init_keys() -> None:
    defaults = {
        "k_openrouter": env("OPENROUTER_API_KEY", default=""),
        "k_or_model": env("OPENROUTER_MODEL", default="anthropic/claude-haiku-4.5"),
        "k_or_base": env("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"),
        "k_wp_url": env("WORDPRESS_URL", default=""),
        "k_wp_user": env("WORDPRESS_USER", default=""),
        "k_wp_pass": env("WORDPRESS_APP_PASSWORD", default=""),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def wp_client() -> WordPressClient:
    return WordPressClient(
        st.session_state["k_wp_url"], st.session_state["k_wp_user"], st.session_state["k_wp_pass"]
    )


# ---------------------------------------------------------------------------
st.set_page_config(page_title="Feeder · Painel", page_icon="🌱", layout="wide")
init_keys()
st.title("🌱 Feeder · Painel")

aba_dados, aba_config = st.tabs(["📊 Dados", "⚙️ Configuração"])

# ======================= ABA DADOS =======================
with aba_dados:
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("▶ Rodar agora", type="primary", width="stretch"):
            with st.spinner("Coletando, classificando e roteando..."):
                st.session_state["report"] = flow.do(build_app())
    rep = st.session_state.get("report")
    with col2:
        if rep:
            st.success(
                f"coletados {rep.coletados} · novos {rep.novos} · "
                f"duplicados {rep.duplicados} · publicados {rep.publicados or '—'}"
            )

    app = build_app()
    itens = app.storage.list_recent(tipo=None, limit=1000)

    f1, f2, f3 = st.columns(3)
    tipo = f1.selectbox("Tipo", ["todos", "evento", "noticia"])
    ufs = sorted({i.uf for i in itens if i.uf})
    uf = f2.selectbox("UF", ["todas", *ufs])
    grupos = sorted({g for i in itens for g in i.grupos})
    grupo = f3.selectbox("Grupo", ["todos", *grupos])

    def ok(i) -> bool:
        if tipo != "todos" and i.tipo.value != tipo:
            return False
        if uf != "todas" and i.uf != uf:
            return False
        return not (grupo != "todos" and grupo not in i.grupos)

    filtrados = [i for i in itens if ok(i)]
    st.caption(f"{len(filtrados)} itens")
    st.dataframe(
        [
            {
                "tipo": i.tipo.value,
                "quando": (i.data_inicio or i.publicado_em or i.coletado_em).date().isoformat(),
                "título": i.titulo,
                "cidade/UF": f"{i.cidade or ''}/{i.uf or ''}".strip("/"),
                "grupos": ", ".join(i.grupos),
                "fonte": i.fonte,
                "url": i.url,
            }
            for i in filtrados
        ],
        width="stretch",
        hide_index=True,
    )

    # ---- Sincronizar eventos com o WordPress ----
    eventos = [i for i in filtrados if i.tipo.value == "evento"]
    with st.expander(f"📤 Sincronizar eventos com o WordPress ({len(eventos)})"):
        wpc = wp_client()
        if not wpc.configured:
            st.warning("Configure as chaves do WordPress na aba ⚙️ Configuração.")
        elif not eventos:
            st.info("Nenhum evento no filtro atual.")
        else:
            por_titulo = {i.titulo: i for i in eventos}
            escolhidos = st.multiselect("Eventos a enviar", list(por_titulo))
            cats = st.session_state.get("wp_categories", [])
            tags = st.session_state.get("wp_tags", [])
            cat_sel = st.multiselect("Categorias (WordPress)", [c["name"] for c in cats])
            tag_sel = st.multiselect("Tags (WordPress)", [t["name"] for t in tags])
            usar_haiku = st.checkbox("Gerar resumo com Haiku se faltar", value=True)
            if not cats and not tags:
                st.caption("Dica: carregue categorias/tags do WP na aba Configuração.")
            if st.button("📤 Enviar para WordPress (rascunho)", type="primary"):
                cat_ids = [c["id"] for c in cats if c["name"] in cat_sel]
                tag_ids = [t["id"] for t in tags if t["name"] in tag_sel]
                clf = FunnelClassifier(
                    grupos=load_config().grupos,
                    api_key=st.session_state["k_openrouter"],
                    base_url=st.session_state["k_or_base"],
                    model=st.session_state["k_or_model"],
                )
                oks, erros = 0, []
                with st.spinner("Enviando..."):
                    for titulo in escolhidos:
                        item = por_titulo[titulo]
                        if usar_haiku and not item.resumo:
                            clf.enrich(item)
                        try:
                            wpc.create_event(item, categories=cat_ids, tags=tag_ids)
                            oks += 1
                        except Exception as exc:  # noqa: BLE001
                            erros.append(f"{titulo}: {exc}")
                if oks:
                    st.success(f"{oks} evento(s) criados como rascunho no WordPress.")
                for e in erros:
                    st.error(e)

# ======================= ABA CONFIG =======================
with aba_config:
    st.subheader("🔑 Chaves de acesso")
    st.caption("Use aqui se não quiser editar o .env à mão. 'Salvar' grava no .env.")
    st.text_input("OpenRouter API Key", type="password", key="k_openrouter")
    st.text_input("OpenRouter modelo", key="k_or_model")
    st.text_input("WordPress URL", key="k_wp_url", placeholder="https://seusite.com.br")
    cwp1, cwp2 = st.columns(2)
    cwp1.text_input("WordPress usuário", key="k_wp_user")
    cwp2.text_input("WordPress App Password", type="password", key="k_wp_pass")
    if st.button("💾 Salvar chaves no .env"):
        update_env(
            ENV_PATH,
            {
                "OPENROUTER_API_KEY": st.session_state["k_openrouter"],
                "OPENROUTER_MODEL": st.session_state["k_or_model"],
                "WORDPRESS_URL": st.session_state["k_wp_url"],
                "WORDPRESS_USER": st.session_state["k_wp_user"],
                "WORDPRESS_APP_PASSWORD": st.session_state["k_wp_pass"],
            },
        )
        st.success(".env atualizado.")

    st.subheader("🏷️ WordPress: categorias e tags")
    st.caption("Puxa do seu WordPress para aplicar nos eventos sincronizados.")
    if st.button("🔄 Carregar categorias/tags do WordPress"):
        wpc = wp_client()
        if not wpc.configured:
            st.warning("Preencha as chaves do WordPress acima primeiro.")
        else:
            try:
                st.session_state["wp_categories"] = wpc.list_categories()
                st.session_state["wp_tags"] = wpc.list_tags()
                st.success(
                    f"{len(st.session_state['wp_categories'])} categorias e "
                    f"{len(st.session_state['wp_tags'])} tags carregadas."
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Falha ao carregar: {exc}")
    if st.session_state.get("wp_categories"):
        st.caption("Categorias: " + ", ".join(c["name"] for c in st.session_state["wp_categories"][:40]))
    if st.session_state.get("wp_tags"):
        st.caption("Tags: " + ", ".join(t["name"] for t in st.session_state["wp_tags"][:40]))

    st.divider()
    raw = load_raw()
    st.subheader("Região")
    regiao = raw.get("regiao", {}) or {}
    ufs_aceitas = st.multiselect(
        "UFs aceitas (vazio = qualquer UF)",
        BR_UFS,
        default=[u for u in (regiao.get("ufs_aceitas") or []) if u in BR_UFS],
    )

    st.subheader("Grupos de interesse")
    st.caption("Keywords separadas por vírgula. Adicione/remova linhas.")
    grupos_edit = st.data_editor(
        [
            {"nome": g.get("nome", ""), "keywords": ", ".join(g.get("keywords", []))}
            for g in raw.get("grupos", [])
        ],
        num_rows="dynamic",
        width="stretch",
        key="grupos_editor",
    )

    st.subheader("Fontes de notícias (RSS)")
    fontes = raw.get("fontes", {}) or {}
    rss_edit = st.data_editor(
        [
            {"id": f.get("id", ""), "url": f.get("url", ""), "grupos": ", ".join(f.get("grupos", []))}
            for f in fontes.get("noticias", [])
        ],
        num_rows="dynamic",
        width="stretch",
        key="rss_editor",
    )
    st.info("Fontes de evento (Even3, Doity, feiras) são editáveis no config.yaml — ver docs/adr.")

    if st.button("💾 Salvar configuração", type="primary"):
        raw.setdefault("regiao", {})["ufs_aceitas"] = ufs_aceitas
        raw["grupos"] = [
            {
                "nome": r["nome"].strip(),
                "keywords": [k.strip() for k in (r.get("keywords") or "").split(",") if k.strip()],
            }
            for r in grupos_edit
            if (r.get("nome") or "").strip()
        ]
        raw.setdefault("fontes", {})["noticias"] = [
            {
                "id": r["id"].strip(),
                "tipo": "rss",
                "url": r["url"].strip(),
                "grupos": [g.strip() for g in (r.get("grupos") or "").split(",") if g.strip()],
            }
            for r in rss_edit
            if (r.get("id") or "").strip() and (r.get("url") or "").strip()
        ]
        save_raw(raw)
        st.success("config.yaml salvo. O próximo 'Rodar agora' já usa a nova config.")
