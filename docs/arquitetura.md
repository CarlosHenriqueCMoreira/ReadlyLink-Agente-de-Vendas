# Arquitetura do projeto

O projeto usa duas camadas de transformação:

1. O ETL em Python lê os CSVs, valida a estrutura, faz a limpeza técnica e carrega o schema `raw`.
2. O dbt normaliza os campos, aplica as regras de negócio e cria as tabelas analíticas.

## Fluxo

    data/usuarios_readly.csv ─┐
    data/catalogo_livros.csv ─┤  extract.py → transform.py → load.py / load_business.py
    data/atendimentos.csv ────┤
    data/vendas.csv ──────────┘
                │
                ▼
    PostgreSQL · raw.usuarios_csv, raw.catalogo_livros, raw.atendimentos, raw.vendas
                │
                ▼  dbt
    staging       stg_usuarios, stg_catalogo_livros, stg_atendimentos, stg_vendas
                │
    intermediate  int_livros_pegos            uma linha por livro retirado (obra + edição)
                  int_perfil_leitura_usuario  gênero, tom e formato preferidos; última saga
                  int_contexto_atendimento    pedido + histórico + livro procurado + recomendação antiga
                  int_candidatos_atendimento  MOTOR DE REGRAS: atendimento × produto disponível
                │
    marts         dim_usuarios, dim_livros, dim_produtos
                  fct_livros_pegos, fct_atendimentos, fct_vendas
                  mart_motivos_abandono       motivos com a evidência de cada um
                  mart_funil_vendas           onde a venda para
                  mart_qualidade_operacional  aceite, conversão, custo, preço/estoque informados
                  mart_recomendacao_atendimento  nova recomendação por atendimento
                  mart_antes_depois           regras cumpridas: agente antigo × regras novas
                  mart_solucoes_atendimento   uma ação por atendimento perdido
                  mart_resultado_solucoes     cobertura automática e revisão humana
                  mart_recomendacoes_usuario  recomendação de catálogo só pelo histórico
                  mart_resumo_usuarios
                │
                ▼
    scripts/exportar_metricas.py  → readly_dbt/target/business_metrics.json
    scripts/escrever_respostas.py → respostas no JSON + docs/respostas_perguntas.md
    readly_dbt/site/ (index.html, app.js, styles.css) → página visual

## Decisões

**A camada raw preserva o formato recebido.** Tudo chega como texto e as
conversões ficam no staging. Isso permite rastrear um erro até à linha do CSV.

**Obra e edição.** No CSV de usuários o mesmo título aparece com dois IDs, um
da edição física e outro da digital. O catálogo identifica o livro pela obra
(saga + volume) e o formato pelo produto. `int_livros_pegos` guarda o ID
original em `edicao_id` e liga cada retirada à obra. Sem isso, "o cliente já
leu" falhava quando o livro tinha sido lido no outro formato.

**Estoque digital.** A origem grava 9999 para "ilimitado". O staging troca por
`estoque = null` e `estoque_ilimitado = true`, e um teste impede que o 9999
volte a aparecer.

**Um único motor de regras.** `int_candidatos_atendimento` calcula, para cada
atendimento e cada produto disponível, as regras de adequação, a pontuação e a
frase de justificativa. A recomendação nova, a comparação antes e depois e as
soluções usam todas o mesmo motor. Por isso uma regra muda num lugar só e os
testes cobrem os três usos.

**O motivo de abandono precisa de evidência.** Os dados simulados representam o
atendimento antigo, e cada motivo é consequência de uma falha visível: preço
acima do orçamento, título indisponível, volume errado ou gosto diferente. Os
testes `motivo_abandono_coerente` e `motivos_tem_evidencia` falham se isso
deixar de ser verdade.

## Camada de solução

Depois de medir os motivos de abandono, o dbt cria:

- `mart_solucoes_atendimento`: uma ação concreta por atendimento sem compra, o livro oferecido, a justificativa e, quando não há opção, o motivo da revisão humana;
- `mart_resultado_solucoes`: cobertura automática e casos para revisão humana por problema;
- `mart_antes_depois`: quanto a recomendação nova cumpre as regras em comparação com a antiga.

A camada não conta uma ação como venda recuperada. O resultado comercial só é
confirmado quando o cliente aceitar a alternativa e concluir a compra. A
comparação antes e depois mede o cumprimento de regras, não vendas.
