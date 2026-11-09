# ADR-0005 — Escalonamento HTTP → Playwright no scraping

- Status: Aceito
- Contexto: parte dos sites de evento renderiza a listagem via JavaScript; outra
  parte entrega HTML direto. Subir um navegador para tudo é lento e caro.

## Decisão

Cada fonte de scraping declara seu **método** no `config.yaml`, e o collector
**escalona por degrau**:

1. **`http`** (padrão) — `httpx` + BeautifulSoup. Leve e rápido. Tenta sempre
   primeiro.
2. **`playwright`** — só para fontes que exigem JS. Liga o navegador apenas
   nessa fonte. (Não implementado no v1 — esqueleto marcado em
   `src/services/collectors/scraper.py`.)
3. **Stealth** (user-agent real, `playwright-stealth`, rate limit) — só se a
   fonte bloquear. É corrida de gato e rato; não blindar preventivamente.

## Consequências

- ✅ Mantém o pipeline rápido: a maioria fica no degrau HTTP.
- ✅ Custo de navegador só onde é inevitável.
- ⚠️ Playwright e stealth adicionam dependências pesadas — entram por fonte, no
  v2, conforme a necessidade real aparecer.
