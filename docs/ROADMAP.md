# 🗺️ Roadmap — Feeder

> Fonte única de pendências. O v1 (POC) está entregue — ver [MVP.md](MVP.md).
> Pegue itens de cima para baixo dentro de cada prioridade.

## Contexto do stack

Repo do ecossistema Kaktu/GaiaCorp. Irmãos no mesmo diretório-pai, referenciados
por caminho relativo. Convenções herdadas de `oxossi` e `witch-doctor`.

## P0 — fechar as trilhas de evento

- [ ] **Trilha B — refresh de data das feiras**: job que lê a data da próxima
  edição no site oficial de cada feira e atualiza sozinho.
- [ ] **Trilha C — parsing real do scraping** por fonte (começar pelo Even3,
  que é o mais aderente ao nicho). Seletores por-fonte em `scraper.py`.
- [ ] **Geolocalização de eventos** (lat/long + cidade/UF) para "eventos
  próximos" de verdade.

## P1 — produção

- [ ] **Agendamento via Prefect** (como no oxossi) — hoje é CLI manual.
- [ ] **API de leitura** para o WordPress consumir as notícias `store_only`.
- [ ] **Modo manutenção por fonte**: quando um scraper quebra, isolar a fonte
  sem derrubar o pipeline.
- [ ] **Playwright + stealth** por fonte, quando uma listagem exigir JS
  (ver [adr/0005](adr/0005-escalonamento-de-scraping.md)).

## P2 — qualidade e escala

- [ ] **Dedup semântico** (via LLM) além do dedup por título normalizado.
- [ ] **Migração SQLite → Postgres** quando volume/consulta justificar.
- [ ] Observabilidade: métricas por fonte (itens/erros/latência).
- [ ] CI (GitHub Actions) rodando ruff + pytest.

## Backlog

- [ ] Serviço de scraping pago (Apify) como fallback de zero-manutenção.
- [ ] Mais grupos de interesse / outros nichos (prova do config-driven).
