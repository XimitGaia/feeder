# ADR-0003 — Injeção de dependência, modos prod/test e o LLM via OpenRouter

- Status: Aceito
- Contexto: o feeder toca serviços externos (RSS, OpenRouter, WordPress, banco).
  Precisa ser testável sem I/O e rodável localmente sem credenciais. A casa usa
  `witch_doctor` para DI (ver oxossi).

## Decisão

Seguir a **filosofia de DI da casa**: interfaces (`I*`) em `src/core/interfaces`,
implementações em `src/services`, um **initializer** escolhe os binds e o
`Injector` (`injector.py`) escolhe o modo em runtime:

| Modo | Initializer | Bind |
|---|---|---|
| `prod` | `src/__init__.py` | serviços reais; lê `.env` |
| `test` | `tests/__init__.py` | stubs de `tests/mocks` (sem I/O) |

**Desvio consciente do witch_doctor no v1:** collectors e sinks são
**múltiplos por interface** (vários collectors; vários sinks), e o
`witch_doctor.register` binda **uma** implementação por interface. Por isso o
initializer é um **composition root** explícito (constrói e expõe um `App` com
as listas/registries), em vez do decorator `@WitchDoctor.injection`. A
filosofia (interfaces/impls/initializer/modo) é preservada; a adoção plena do
witch_doctor para os serviços singulares fica para o v2.

**Classificação via OpenRouter → Claude Haiku:** o LLM é acessado por OpenRouter
(API compatível com OpenAI). Modelo barato/rápido (`anthropic/claude-haiku-4.5`)
porque o funil (ADR-0002) já reduz muito o volume que chega nele. Sem
`OPENROUTER_API_KEY`, a etapa de LLM é pulada — o feeder **degrada para
só-keyword** e roda sem credencial.

## Consequências

- ✅ Testes rodam sem rede nem disco (modo `test`).
- ✅ v1 roda sem nenhuma credencial (LLM e WP viram no-op).
- ✅ Custo de LLM baixo: só itens que passam no funil, modelo Haiku.
- ⚠️ Composition root manual diverge do uso canônico do witch_doctor — anotado
  para revisitar no v2.
