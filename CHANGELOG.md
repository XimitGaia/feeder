# Changelog

## [Unreleased]

### Added
- Trilha C — **Even3 funcional** via JSON estruturado (Azure Blob), categoria
  "Agricultura, pesca e veterinária". Coleta eventos reais de agro com cidade/UF,
  datas, local e imagem; filtra passados e por região. Ver `docs/adr/0007`.
- `Even3Collector` + testes sem rede; config `tipo: even3` com `categorias`.

## [0.1.0] — 2026-11-09

Marco inicial (POC v1). Ver [docs/MVP.md](docs/MVP.md).

### Added
- Pipeline: coleta → classifica → deduplica → persiste → sinks.
- Trilha A (notícias RSS) funcional — validada com 151 notícias reais.
- Funil de classificação keyword → Claude Haiku (OpenRouter); degrada para
  só-keyword sem credencial.
- Dedup por mescla; persistência SQLite idempotente.
- Sinks por tipo de conteúdo: `evento→wordpress_draft`, `noticia→store_only`.
- CLI (`run`, `sources`), DI com modos prod/test, testes sem I/O.
- Docs: MVP, ROADMAP, 6 ADRs, CLAUDE.md.
- Trilha B (feiras) com seed cadastrado; Trilha C (scraping) em stub.
