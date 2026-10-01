-- Um motivo de abandono só pode existir quando a causa aparece nos dados.

select atendimento_id, motivo_abandono
from {{ ref('int_contexto_atendimento') }}
where
    (motivo_abandono = 'preco_acima_do_orcamento' and preco_informado <= orcamento)
    or (
        motivo_abandono = 'livro_procurado_sem_estoque'
        and (livro_procurado_id is null or procurado_disponivel_no_formato)
    )
    or (
        motivo_abandono = 'nao_encontrou_continuacao'
        and livro_recomendado_id = livro_procurado_id
    )
    or (resultado = 'VENDA_CONCLUIDA' and motivo_abandono is not null)
    or (resultado = 'SEM_COMPRA' and motivo_abandono is null)
