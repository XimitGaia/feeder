# ADR-0007 — Even3: coletar via JSON estruturado, não scraping de HTML

- Status: Aceito
- Contexto: a Trilha C (eventos) precisava de uma fonte real. A API oficial do
  Even3 não serve para descoberta (ver [ADR-0004](0004-apis-de-eventos.md)). A
  página de listagem (`/eventos/?busca=...`) é uma landing com carrosséis cujos
  cards são **templates AngularJS** (`{{item.titulo}}`) — o HTML não contém os
  dados, que são carregados por XHR.

## Decisão

Ao investigar de onde o Angular busca os dados, achamos que a home é alimentada
por **JSONs estáticos no Azure Blob**. Usar:

```
https://even3v2.blob.core.windows.net/json/home-lista_evento.json
```

Esse arquivo responde **sem parâmetro de versão** e traz:
- `listaCategorias` — 12 categorias (id, descrição, url).
- `listaEventosPorCategoria` — eventos agrupados por categoria, cada evento com
  campos ricos: `titulo`, `url`, `data`/`dataFim`, `cidade`, `siglaEstado`,
  `localRealizacao`, `resumoEvento`, `urlImagemBanner`, `passou`, etc.

A categoria **`id=1` ("Agricultura, pesca e veterinária")** é o nosso agro. O
`Even3Collector` filtra por `idCategoria`, descarta eventos com `passou=true`
(feed é agenda) e mapeia cada evento para `Item(tipo=evento)`. O filtro de
região (SP) é aplicado depois, no flow, via `siglaEstado` — eventos online
(sem UF) passam.

## Consequências

- ✅ Dado **estruturado e limpo** — nada de raspar template HTML frágil.
- ✅ Já validado: coletou eventos reais de agro em SP (ex.: curso de
  fertilizantes na ESALQ-USP; JOIA 2026 na Unesp/Botucatu).
- ⚠️ Cobertura: combinamos dois blobs ungated por categoria —
  `lista_de_eventos-categoria-{id}.json` (`listaEventosPorCategoriaPaginados`) +
  o bloco da categoria em `home-lista_evento.json` — e deduplicamos por `id`.
  Isso elevou a categoria agro de ~12 para ~23 eventos. Os blobs
  `home-eventosporestado-brasil-<uf>.json` retornam 404 (não publicados).
- ⚠️ O **catálogo completo** só está atrás de `/auxiliar/retornarlistaevento/`,
  que é **protegido por reCAPTCHA v3 + token anti-forgery** (POST retorna
  `Object:[]` sem token válido). Puxá-lo exige Playwright para obter o token —
  trabalho de v2 (escalonamento do [ADR-0005](0005-escalonamento-de-scraping.md)).
- ⚠️ É um JSON **não documentado/interno** do Even3 — pode mudar sem aviso. O
  collector degrada para lista vazia em erro, sem derrubar o pipeline. Os blobs
  `home-eventosporestado-brasil-<uf>.json` exigem um `?v=<guid>` dinâmico (lido
  da página) e ficam como alternativa para v2 se quisermos filtrar por UF na
  origem.
