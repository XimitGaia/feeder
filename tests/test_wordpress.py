"""Testes do render do WordPress (sem rede)."""

from __future__ import annotations

from datetime import datetime

from src.core.models import ContentType, Item
from src.services.sinks.wordpress import render_item_html


def test_evento_render_tem_foto_data_local_e_link_oficial():
    item = Item(
        tipo=ContentType.EVENTO,
        titulo="Agrishow 2027",
        descricao="Feira de tecnologia agrícola.",
        url="https://www.agrishow.com.br/",
        fonte="agrishow",
        imagem="https://img/banner.jpg",
        data_inicio=datetime(2027, 4, 26),
        data_fim=datetime(2027, 4, 30),
        cidade="Ribeirão Preto",
        uf="SP",
    )
    html = render_item_html(item)
    assert '<img src="https://img/banner.jpg"' in html
    assert "2027-04-26 a 2027-04-30" in html
    assert "Ribeirão Preto, SP" in html
    assert 'href="https://www.agrishow.com.br/"' in html
    assert "Página oficial do evento" in html


def test_evento_usa_resumo_haiku_quando_tem():
    item = Item(
        tipo=ContentType.EVENTO,
        titulo="Curso",
        descricao="descrição longa do feed",
        resumo="resumo curto do haiku",
        url="https://x",
        fonte="even3",
    )
    assert "resumo curto do haiku" in render_item_html(item)


def test_noticia_render_usa_resumo_simples():
    item = Item(
        tipo=ContentType.NOTICIA,
        titulo="Safra recorde",
        descricao="texto longo",
        resumo="resumo curto",
        url="https://x",
        fonte="rss",
    )
    assert render_item_html(item) == "resumo curto"
