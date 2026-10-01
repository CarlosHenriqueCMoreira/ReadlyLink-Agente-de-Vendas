-- Junta, para cada atendimento, o que o cliente pediu, o histórico dele,
-- o livro que ele procurava e o que o agente antigo recomendou.
-- Uma linha por atendimento.

with atendimentos as (
    select * from {{ ref('stg_atendimentos') }}
),

livros as (
    select * from {{ ref('dim_livros') }}
),

produtos as (
    select * from {{ ref('dim_produtos') }}
),

-- Uma linha por saga: gênero, tom e último volume que existe.
sagas as (
    select saga, genero, tom, max(volume) as volume_final
    from livros
    group by saga, genero, tom
)

select
    atendimentos.*,

    -- Histórico do usuário
    perfil.genero_preferido,
    perfil.tom_preferido,
    perfil.formato_preferido,
    perfil.ultima_saga,
    perfil.ultimo_volume_lido,
    perfil.ultimo_volume_lido >= sagas.volume_final as saga_concluida,
    sagas.genero as genero_ultima_saga,
    sagas.tom as tom_ultima_saga,

    -- Livro que o cliente procurava (título específico ou próximo volume)
    procurado.titulo as titulo_procurado,
    procurado.saga as saga_procurada,
    procurado.volume as volume_procurado,
    procurado.genero as genero_procurado,
    coalesce(produto_procurado.disponivel, false)
        as procurado_disponivel_no_formato,

    -- O que o agente antigo recomendou
    recomendado.titulo as titulo_recomendado,
    recomendado.saga as saga_recomendada,
    recomendado.volume as volume_recomendado,
    recomendado.genero as genero_recomendado,
    recomendado.tom as tom_recomendado

from atendimentos
join {{ ref('int_perfil_leitura_usuario') }} as perfil
    on perfil.usuario_id = atendimentos.usuario_id
join sagas
    on sagas.saga = perfil.ultima_saga
left join livros as procurado
    on procurado.livro_id = atendimentos.livro_procurado_id
left join produtos as produto_procurado
    on produto_procurado.livro_id = atendimentos.livro_procurado_id
   and produto_procurado.formato = atendimentos.formato_desejado
join livros as recomendado
    on recomendado.livro_id = atendimentos.livro_recomendado_id
