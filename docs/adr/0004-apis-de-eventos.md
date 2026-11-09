# ADR-0004 — APIs de Sympla/Eventbrite/Even3 não servem para descoberta

- Status: Aceito
- Contexto: a parte mais valiosa é "eventos próximos". A hipótese inicial era
  puxar eventos dessas plataformas via API oficial.

## Decisão

**Não usar as APIs oficiais para descobrir eventos de terceiros** — elas não
fazem isso. Verificado (nov/2026):

| Plataforma | Busca pública na API? | O que libera |
|---|---|---|
| **Eventbrite** | ❌ desativada desde 2019/2020 | só eventos do dono do token |
| **Sympla** | ❌ | só eventos vinculados ao token (ingressos/pedidos) |
| **Even3** | ❌ chave por evento | só os eventos do dono |

Todas são feitas para o **organizador gerenciar os próprios eventos**. São
gratuitas, mas isso é irrelevante: não expõem catálogo de terceiros.

Consequência prática: a **descoberta** de eventos sai de:
1. **Seed + refresh** das grandes feiras (Trilha B) — poucas, estáveis.
2. **Scraping** das páginas de listagem (Trilha C) — Even3 é o mais valioso
   para o nicho (congressos técnicos de agronomia, ex. CONAGRO).
3. Opcionalmente, serviços de scraping pagos (ex. Apify) se quisermos zero
   manutenção — fora do v1.

## Consequências

- ✅ Não se perde tempo integrando APIs que não entregam o que precisamos.
- ⚠️ Scraping tem custo de manutenção (layout muda) — mitigado pelo isolamento
  por fonte (ADR-0001) e pelo escalonamento (ADR-0005).
- ⚠️ Respeitar `robots.txt` e rate limit é obrigatório para sustentabilidade.

Fontes: Eventbrite search API shutdown (2019/2020); docs Sympla
(developers.sympla.com.br); docs Even3 (docs.even3.com.br).
