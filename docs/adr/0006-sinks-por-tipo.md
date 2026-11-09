# ADR-0006 — Sinks por tipo de conteúdo

- Status: Aceito
- Contexto: nem todo conteúdo coletado deve ir para o mesmo lugar. Eventos a
  gente quer publicar (como rascunho, para curadoria); notícias **não** são
  publicadas no WordPress — serão consumidas de outra forma (ex.: pautas via
  consulta ao banco / uma API futura).

## Decisão

Destinos (**sinks**) são declarados por **tipo de conteúdo** no `config.yaml`,
com possibilidade de **override por fonte**:

```yaml
sinks:
  evento:  [wordpress_draft]   # cria post rascunho via REST API do WP
  noticia: [store_only]        # só persiste; nada é publicado
```

Sinks disponíveis no v1:
- **`wordpress_draft`** — cria o post como `draft` via REST API (Application
  Password). Curadoria humana publica depois.
- **`store_only`** — no-op de publicação; o item fica só no banco.

A resolução vive em `Config.sinks_para(tipo, override)`: o override da fonte
vence o padrão do tipo. O flow persiste **todos** os itens (IStorage) e depois
roteia cada um para os sinks do seu tipo.

## Consequências

- ✅ A regra "evento publica, notícia não" é **configuração**, não código.
- ✅ Adicionar um destino novo (ex.: webhook, fila) é implementar um `ISink` e
  referenciá-lo no YAML.
- ✅ Publicar como rascunho mantém curadoria humana no loop (segurança do v1).
- ⚠️ `store_only` depende de um consumidor externo (API de leitura) que ainda
  não existe — está no ROADMAP.
