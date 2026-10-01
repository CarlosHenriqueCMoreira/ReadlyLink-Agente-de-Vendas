-- FUNIL DE VENDAS
-- Quantos atendimentos chegaram a cada etapa e quantos se perderam nela.

with totais as (
    select
        count(*) as atendimentos,
        sum(case when etapa_final <> 'BUSCA' then 1 else 0 end) as passaram_da_busca,
        sum(case when recomendacao_aceita then 1 else 0 end) as chegaram_ao_checkout,
        sum(case when resultado = 'VENDA_CONCLUIDA' then 1 else 0 end) as vendas
    from {{ ref('fct_atendimentos') }}
),

funil as (
    select 1 as ordem, 'Atendimentos iniciados' as etapa, atendimentos as quantidade from totais
    union all
    select 2, 'Encontraram o que procuravam (passaram da busca)', passaram_da_busca from totais
    union all
    select 3, 'Aceitaram a recomendação (chegaram ao checkout)', chegaram_ao_checkout from totais
    union all
    select 4, 'Venda concluída (pagamento e aprovação humana)', vendas from totais
)

select
    ordem,
    etapa,
    quantidade,
    -- first_value = quantidade da primeira etapa; lag = quantidade da etapa anterior.
    round(100.0 * quantidade / first_value(quantidade) over (order by ordem), 1) as percentual_inicial,
    round(100.0 * quantidade / lag(quantidade) over (order by ordem), 1) as percentual_etapa_anterior,
    lag(quantidade) over (order by ordem) - quantidade as perdidos_nesta_etapa
from funil
order by ordem
