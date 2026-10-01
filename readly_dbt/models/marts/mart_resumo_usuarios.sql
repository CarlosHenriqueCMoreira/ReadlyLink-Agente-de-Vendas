-- RESUMO ANALÍTICO POR USUÁRIO
-- Junta usuários e retiradas para responder perguntas de negócio.

select
    usuarios.usuario_id,
    usuarios.nome_completo,

    -- Quantos títulos diferentes o usuário retirou.
    count(distinct fatos.livro_id) as livros_distintos,

    -- Quantidade total de exemplares retirados.
    coalesce(sum(fatos.quantidade), 0) as exemplares_retirados,

    -- Período de atividade do usuário.
    min(fatos.data_retirada) as primeira_retirada,
    max(fatos.data_retirada) as ultima_retirada

from {{ ref('dim_usuarios') }} as usuarios

left join {{ ref('fct_livros_pegos') }} as fatos
    on usuarios.usuario_id = fatos.usuario_id

group by
    usuarios.usuario_id,
    usuarios.nome_completo
