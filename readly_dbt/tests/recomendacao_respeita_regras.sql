-- A nova recomendação nunca pode violar as regras de livro adequado.

select novo.atendimento_id
from {{ ref('mart_recomendacao_atendimento') }} as novo
join {{ ref('int_candidatos_atendimento') }} as candidatos
    on candidatos.atendimento_id = novo.atendimento_id
   and candidatos.produto_id = novo.produto_id
where not candidatos.adequado

union all

-- A recomendação de catálogo também não pode repetir leitura nem pular volume.
select cast(recomendacoes.usuario_id as text)
from {{ ref('mart_recomendacoes_usuario') }} as recomendacoes
where exists (
        select 1 from {{ ref('fct_livros_pegos') }} as lidos
        where lidos.usuario_id = recomendacoes.usuario_id
          and lidos.livro_id = recomendacoes.livro_id
    )
   or (
        recomendacoes.volume > 1
        and not exists (
            select 1 from {{ ref('fct_livros_pegos') }} as lidos
            where lidos.usuario_id = recomendacoes.usuario_id
              and lidos.saga = recomendacoes.saga
              and lidos.volume = recomendacoes.volume - 1
        )
    )
