# ADR-0002 — Grupos de interesse orientados a config

- Status: Aceito
- Contexto: hoje o foco é agro/plantas/jardinagem, mas a intenção é reaproveitar
  o feeder para outros temas/clientes depois. Hardcodar "agro" no código
  engessaria isso.

## Decisão

Um **grupo de interesse** é um objeto declarado no `config.yaml`:

```yaml
grupos:
  - nome: agronomia
    keywords: [agronomia, agro, plantio, safra, ...]
```

Cada `Item` coletado é **casado** com um ou mais grupos na etapa de
classificação. Cadastrar um grupo novo faz o feeder passar a classificar itens
nele — **sem tocar em código**. Fontes também declaram a quais grupos alimentam,
servindo de palpite inicial que o classificador confirma/ajusta.

O casamento é um **funil** (ver [ADR-0003](0003-di-e-modos.md) para o LLM):
1. **keyword** (barato) — peneira grossa; item fora de todo grupo é descartado.
2. **LLM** (Haiku) — só no que passou, para desambiguar e enriquecer.

## Consequências

- ✅ Sistema genérico: outro nicho = novo grupo no YAML.
- ✅ 80% do ruído cai no filtro de keyword, a custo zero.
- ⚠️ Keywords ruins = falsos positivos/negativos; a curadoria das keywords por
  grupo importa. O LLM mitiga, mas não substitui, boas keywords.
