"""Testes do pipeline sem I/O (usa o test_initializer com stubs)."""

from __future__ import annotations

from src.core.models import ContentType, Item
from src.flows.feeder_run import flow
from src.services.dedup.dedup import MergeDedup, dedup_key_for
from tests import test_initializer as build_test_app


def test_keyword_funnel_descarta_fora_do_interesse():
    app = build_test_app()
    report = flow.do(app)
    # Das 2 notícias do stub, só a de irrigação/agro passa no funil.
    assert report.coletados == 2
    assert report.classificados == 1
    assert report.novos == 1


def test_noticia_vai_para_store_only_e_nao_publica_no_wp():
    app = build_test_app()
    flow.do(app)
    wp = app.sinks["wordpress_draft"]
    # notícia -> store_only (config); WordPress não recebe nada.
    assert getattr(wp, "published", []) == []


def test_dedup_mantem_registro_mais_rico():
    pobre = Item(tipo=ContentType.NOTICIA, titulo="Safra recorde", url="a", fonte="x")
    rico = Item(
        tipo=ContentType.NOTICIA,
        titulo="Safra recorde",
        descricao="texto",
        imagem="img",
        url="b",
        fonte="y",
    )
    out = MergeDedup().dedupe([pobre, rico])
    assert len(out) == 1
    assert out[0].descricao == "texto"


def test_dedup_key_normaliza_titulo():
    a = Item(tipo=ContentType.NOTICIA, titulo="Safra  Recorde!", url="a", fonte="x")
    b = Item(tipo=ContentType.NOTICIA, titulo="safra recorde", url="b", fonte="y")
    assert dedup_key_for(a) == dedup_key_for(b)
