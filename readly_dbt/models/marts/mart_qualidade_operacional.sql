-- INDICADORES DO ATENDIMENTO ANTIGO
-- Aceite, conversão, custo e se o agente informou preço e estoque iguais aos do banco.

with validacao as (
    select
        atendimentos.*,
        produtos.preco as preco_banco,
        produtos.disponivel
    from {{ ref('fct_atendimentos') }} as atendimentos
    join {{ ref('dim_produtos') }} as produtos
        on atendimentos.produto_recomendado_id = produtos.produto_id
)

select
    count(*) as atendimentos,
    sum(case when recomendacao_aceita then 1 else 0 end) as recomendacoes_aceitas,
    round(100.0 * sum(case when recomendacao_aceita then 1 else 0 end) / count(*), 1)
        as taxa_aceitacao_percentual,
    sum(case when resultado = 'VENDA_CONCLUIDA' then 1 else 0 end) as vendas_concluidas,
    round(100.0 * sum(case when resultado = 'VENDA_CONCLUIDA' then 1 else 0 end) / count(*), 1)
        as conversao_percentual,
    sum(case when preco_informado <> preco_banco then 1 else 0 end) as divergencias_preco,
    sum(case when not disponivel then 1 else 0 end) as recomendacoes_sem_estoque,
    sum(case when preco_informado > orcamento then 1 else 0 end) as recomendacoes_acima_orcamento,
    round(sum(custo_ia_eur), 2) as custo_total_ia_eur,
    round(avg(custo_ia_eur), 4) as custo_medio_atendimento_eur,
    round(avg(avaliacao), 2) as avaliacao_media,
    -- avg ignora nulos: o case sem else devolve nulo para as outras linhas.
    round(avg(case when resultado = 'VENDA_CONCLUIDA' then avaliacao end), 2)
        as avaliacao_media_com_compra,
    round(avg(case when resultado = 'SEM_COMPRA' then avaliacao end), 2)
        as avaliacao_media_sem_compra
from validacao
