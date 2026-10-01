-- NOVA RECOMENDAÇÃO (o "depois")
-- Para cada atendimento, o melhor livro ADEQUADO segundo o motor de regras.
-- Quando nenhum livro cumpre as regras, o atendimento vai para uma pessoa.

with contexto as (
    select * from {{ ref('int_contexto_atendimento') }}
),

ranking as (
    select
        candidatos.*,
        row_number() over (
            partition by atendimento_id
            -- O livro que o cliente pediu vem primeiro; depois a pontuação.
            order by e_livro_procurado desc, pontuacao desc, preco, produto_id
        ) as posicao
    from {{ ref('int_candidatos_atendimento') }} as candidatos
    where adequado
)

select
    contexto.atendimento_id,
    contexto.usuario_id,
    contexto.intencao,
    contexto.necessidade_declarada,
    contexto.para_quem,
    contexto.genero_desejado,
    contexto.tom_desejado,
    contexto.formato_desejado,
    contexto.orcamento,
    contexto.livro_procurado_id,
    contexto.titulo_procurado,
    contexto.ultima_saga,
    contexto.ultimo_volume_lido,
    contexto.motivo_abandono,

    -- Antes: o que o agente antigo ofereceu
    contexto.titulo_recomendado as titulo_antes,
    contexto.formato_recomendado as formato_antes,
    contexto.preco_informado as preco_antes,

    -- Depois: o que as regras novas oferecem
    ranking.produto_id,
    ranking.livro_id,
    ranking.titulo,
    ranking.saga,
    ranking.volume,
    ranking.genero,
    ranking.tom,
    ranking.formato,
    ranking.preco,
    ranking.estoque,
    ranking.estoque_ilimitado,
    ranking.pontuacao,
    ranking.pontos_genero,
    ranking.pontos_tom,
    ranking.pontos_formato,
    ranking.pontos_livro_procurado,
    ranking.pontos_preco,
    ranking.justificativa,
    ranking.produto_id is not null as recomendacao_encontrada

from contexto
left join ranking
    on ranking.atendimento_id = contexto.atendimento_id
   and ranking.posicao = 1
