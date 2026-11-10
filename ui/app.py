"""Painel do feeder (Streamlit) — ferramenta interna leve.

Três capacidades (ver docs/adr/0010):
  1. Ver os dados coletados (eventos/notícias) com filtros;
  2. Disparar o pipeline (botão "Rodar agora");
  3. Editar a configuração (grupos, região, fontes RSS) — grava no config.yaml.

Rodar:  uv run --group ui streamlit run ui/app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml
from decouple import config as env

from src import initializer
from src.core.config import load_config
from src.flows.feeder_run import flow

CONFIG_PATH = Path(env("CONFIG_PATH", default="config.yaml"))
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


# ---------------------------------------------------------------------------
st.set_page_config(page_title="Feeder · Painel", page_icon="🌱", layout="wide")
st.title("🌱 Feeder · Painel")

aba_dados, aba_config = st.tabs(["📊 Dados", "⚙️ Configuração"])

# ======================= ABA DADOS =======================
with aba_dados:
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("▶ Rodar agora", type="primary", width="stretch"):
            with st.spinner("Coletando, classificando e roteando..."):
                report = flow.do(build_app())
            st.session_state["report"] = report
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

# ======================= ABA CONFIG =======================
with aba_config:
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
