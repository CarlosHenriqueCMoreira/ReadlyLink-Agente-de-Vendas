-- RESUMO DAS SOLUÇÕES POR MOTIVO DE ABANDONO
-- Quantos casos tiveram ação automática e quantos precisam de uma pessoa.

select
    motivo_abandono,
    count(*) as casos_encontrados,
    sum(case when solucao_gerada then 1 else 0 end) as casos_com_solucao,
    sum(case when status_solucao = 'REVISAO_HUMANA' then 1 else 0 end) as casos_para_revisao_humana,
    round(100.0 * sum(case when solucao_gerada then 1 else 0 end) / count(*), 1) as cobertura_percentual,
    string_agg(distinct acao_gerada, ', ' order by acao_gerada) as acoes_utilizadas,
    round(avg(preco_solucao), 2) as preco_medio_solucao,
    round(avg(orcamento), 2) as orcamento_medio
from {{ ref('mart_solucoes_atendimento') }}
group by motivo_abandono
order by casos_encontrados desc
