# ADR-0008 — Grandes feiras: seed manual + refresh de data (Trilha B)

- Status: Aceito
- Contexto: as grandes feiras do agro (Agrishow, Hortitec, Expointer, ...) são
  eventos âncora, poucos e estáveis, mas não aparecem de forma confiável nas
  fontes automáticas (Even3 etc.). Precisamos delas na agenda com datas corretas.

## Decisão

Padrão **seed + refresh**:
- **Seed** (manual, uma vez): cada feira é cadastrada no `config.yaml`
  (`fontes.feiras_recorrentes`) com nome, site oficial, local/cidade/UF, grupos
  e a **data da próxima edição**.
- **Refresh** (v2): um job lê a data da próxima edição no site oficial e atualiza
  sozinho. No v1 a data é semeada à mão, confirmada por busca.

O `FeirasCollector` emite `Item(tipo=evento)` **apenas** para feiras com
`data_inicio` **futura** — o feed é agenda, não histórico. Feira sem data (ex.:
edição ainda não anunciada) fica fora até ser preenchida.

Seed inicial (confirmar nos sites oficiais):
- **Agrishow 2027** — 26 a 30/abr/2027, Ribeirão Preto/SP. ✅ (futura, emitida)
- **Hortitec** — 31ª ed. foi 17–19/jun/2026 (passou); 2027 sem data oficial →
  fica fora da agenda até a data sair.

## Consequências

- ✅ Cadastra-se o **nome** uma vez; a edição nova entra ao atualizar a data.
- ✅ Datas corretas e sob controle (curadoria humana), sem depender de scraping
  frágil para os eventos mais importantes.
- ⚠️ No v1 a atualização é manual — se ninguém preencher a próxima edição, a
  feira some da agenda depois que a data passa (comportamento proposital).
- ⚠️ O refresh automático (v2) vai precisar de um parser por site (cada feira
  publica a data num formato diferente).
