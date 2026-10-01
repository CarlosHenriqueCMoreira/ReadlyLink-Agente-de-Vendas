-- Toda solução automática precisa estar disponível, caber no orçamento,
-- não repetir um livro já lido e não pular volume de saga
-- (exceto quando é o livro que o próprio cliente pediu).

with solucoes as (
    select *
    from {{ ref('mart_solucoes_atendimento') }}
    where solucao_gerada
)

select solucoes.atendimento_id, solucoes.produto_solucao_id
from solucoes
left join {{ ref('int_candidatos_atendimento') }} as candidatos
    on candidatos.atendimento_id = solucoes.atendimento_id
   and candidatos.produto_id = solucoes.produto_solucao_id
where candidatos.produto_id is null          -- produto indisponível
   or not candidatos.dentro_orcamento
   or candidatos.ja_lido
   or (not candidatos.volume_ok and not candidatos.e_livro_procurado)
