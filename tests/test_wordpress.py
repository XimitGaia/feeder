"""Testes do render do sink WordPress (sem rede)."""

from __future__ import annotations

from datetime import datetime

from src.core.models import ContentType, Item
from src.services.sinks.wordpress import WordPressDraftSink

_SINK = WordPressDraftSink(base_url="", user="u", app_password="p")


def test_evento_render_tem_data_local_e_link():
    item = Item(
        tipo=ContentType.EVENTO,
        titulo="Agrishow 2027",
        descricao="Feira de tecnologia agrícola.",
        url="https://www.agrishow.com.br/",
        fonte="agrishow",
        data_inicio=datetime(2027, 4, 26),
        data_fim=datetime(2027, 4, 30),
        cidade="Ribeirão Preto",
        uf="SP",
    )
    html = WordPressDraftSink._render_content(item)
    assert "2027-04-26 a 2027-04-30" in html
    assert "Ribeirão Preto, SP" in html
    assert 'href="https://www.agrishow.com.br/"' in html
    assert "Feira de tecnologia agrícola." in html


def test_noticia_render_usa_resumo_simples():
    item = Item(
        tipo=ContentType.NOTICIA,
        titulo="Safra recorde",
        descricao="texto longo",
        resumo="resumo curto",
        url="https://x",
        fonte="rss",
    )
    assert WordPressDraftSink._render_content(item) == "resumo curto"
