# ADR-0009 — Doity como 2ª plataforma de eventos (via JSON-LD das páginas)

- Status: Aceito
- Contexto: o Even3 era a única fonte de eventos "de plataforma". Queríamos uma
  segunda, do mesmo tipo (puxada automaticamente). Avaliamos Doity, Embrapa e
  Sebrae.

## Decisão

Adotar o **Doity**. Comparação:

| Candidato | Acesso | Veredito |
|---|---|---|
| **Doity** | Next.js sem JSON público, mas cada página de evento tem `schema.org/Event` em JSON-LD **muito completo**; listagem server-rendered, sem captcha | ✅ escolhido |
| Embrapa | portal de eventos renderizado via JS (`window.__`) | 🟡 exigiria Playwright |
| Sebrae | não expõe listagem de eventos | ❌ |

O `DoityCollector` opera em 2 etapas (http puro):
1. `/eventos?q=<termo>` → coleta URLs dos cards (o Doity filtra por **texto**,
   não por área; buscamos pelos `termos` do grupo);
2. cada URL → lê o JSON-LD `Event` da página → mapeia para `Item`.

Campos obtidos (mais ricos que o Even3): `name`, `description` (texto completo),
`startDate`/`endDate`, `location` (nome + `addressLocality`/`addressRegion` →
cidade/UF), `image`, `organizer`, `offers`. A data vem fora do ISO padrão (ex.:
`2026-11-18-0314:00`) e é extraída por regex.

## Consequências

- ✅ Segunda plataforma de eventos, automática e com campos ricos (descrição
  completa, endereço, imagem).
- ✅ Sem captcha; http puro (degrau 1 do [ADR-0005](0005-escalonamento-de-scraping.md)).
- ⚠️ **Volume baixo**: a busca textual do Doity é restrita — hoje retorna poucos
  eventos de agro (bem menos que o Even3). É complementar, não substituto.
- ⚠️ **Custo de 2 requisições por evento** (listagem + página). Mitigado por
  `max_eventos` e por rodar poucas vezes ao dia.
- ⚠️ Depende do JSON-LD da página (pode mudar). O collector degrada para vazio
  em erro, sem derrubar o pipeline.
