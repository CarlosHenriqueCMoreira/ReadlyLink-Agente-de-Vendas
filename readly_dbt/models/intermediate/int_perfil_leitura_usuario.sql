-- Resume o histórico de cada usuário: gostos e ponto atual da última saga.
-- Uma linha por usuário.

with historico as (
    select
        retiradas.usuario_id,
        retiradas.data_retirada,
        retiradas.quantidade,
        retiradas.formato,
        livros.livro_id,
        livros.saga,
        livros.volume,
        livros.genero,
        livros.tom
    from {{ ref('int_livros_pegos') }} as retiradas
    join {{ ref('dim_livros') }} as livros
        on retiradas.livro_id = livros.livro_id
),

generos as (
    select
        usuario_id,
        genero,
        row_number() over (
            partition by usuario_id
            order by sum(quantidade) desc, genero
        ) as posicao
    from historico
    group by usuario_id, genero
),

formatos as (
    select
        usuario_id,
        formato,
        row_number() over (
            partition by usuario_id
            order by sum(quantidade) desc, formato
        ) as posicao
    from historico
    group by usuario_id, formato
),

tons as (
    select
        usuario_id,
        tom,
        row_number() over (
            partition by usuario_id
            order by sum(quantidade) desc, tom
        ) as posicao
    from historico
    group by usuario_id, tom
),

ultima_retirada as (
    select
        usuario_id,
        saga,
        row_number() over (
            partition by usuario_id
            order by data_retirada desc, volume desc
        ) as posicao
    from historico
),

ultima_saga as (
    -- Na última saga lida, guarda o volume mais alto que o usuário já leu.
    select
        ultima_retirada.usuario_id,
        ultima_retirada.saga as ultima_saga,
        max(historico.volume) as ultimo_volume_lido
    from ultima_retirada
    join historico
        on historico.usuario_id = ultima_retirada.usuario_id
       and historico.saga = ultima_retirada.saga
    where ultima_retirada.posicao = 1
    group by ultima_retirada.usuario_id, ultima_retirada.saga
),

totais as (
    select
        usuario_id,
        count(distinct livro_id) as livros_lidos
    from historico
    group by usuario_id
)

select
    generos.usuario_id,
    generos.genero as genero_preferido,
    tons.tom as tom_preferido,
    formatos.formato as formato_preferido,
    ultima_saga.ultima_saga,
    ultima_saga.ultimo_volume_lido,
    totais.livros_lidos

from generos
join formatos
    on formatos.usuario_id = generos.usuario_id
   and formatos.posicao = 1
join tons
    on tons.usuario_id = generos.usuario_id
   and tons.posicao = 1
join ultima_saga
    on ultima_saga.usuario_id = generos.usuario_id
join totais
    on totais.usuario_id = generos.usuario_id
where generos.posicao = 1
