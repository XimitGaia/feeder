# ADR-0001 — Arquitetura em pipeline e três trilhas de coleta

- Status: Aceito
- Contexto: precisamos reunir, de fontes heterogêneas, **notícias** (fluxo
  contínuo) e **eventos** (agenda) sobre agro/plantas/jardinagem, normalizar e
  entregar prontos para o WordPress e outros consumidores. Fontes têm naturezas
  muito diferentes (RSS limpo, grandes feiras estáveis, listagens só em HTML).

## Decisão

Pipeline linear de 5 etapas, cada uma atrás de uma interface (`I*`):

```
coleta (ICollector) → classifica (IClassifier) → deduplica (IDedup)
  → persiste (IStorage) → sinks (ISink)
```

Tudo que é coletado vira um **`Item`** único (schema em `src/core/models.py`),
com `tipo` ∈ {`noticia`, `evento`} para tratar fluxo vs. agenda.

A coleta se divide em **três trilhas**, cada uma com a técnica certa:

| Trilha | Fonte | Técnica | Estado v1 |
|---|---|---|---|
| **A** | Notícias | RSS/Atom (feedparser) | ✅ funcional |
| **B** | Grandes feiras | seed manual + refresh de data | 🟡 seed |
| **C** | Eventos diversos | scraping de listagem | 🟡 stub |

Dedup é **por mescla**: ao colidir (mesma `dedup_key`, derivada do título
normalizado), mantém-se o registro mais rico em vez de descartar.

A **região** é um parâmetro (`config.yaml → regiao`), não algo hardcoded:
começa em SP e expande trocando a lista.

## Consequências

- ✅ Cada fonte é isolada: se um scraper quebra, notícias e feiras seguem.
- ✅ Schema único simplifica dedup/classificação/sinks.
- ✅ Expandir região/grupo é configuração, não código.
- ⚠️ Pipeline síncrono no v1 (CLI). Paralelismo/agendamento (Prefect) é v2.
