-- Padroniza os pedidos simulados concluídos durante o atendimento.

select
    trim(pedido_id) as pedido_id,
    trim(atendimento_id) as atendimento_id,
    cast(usuario_id as integer) as usuario_id,
    trim(produto_id) as produto_id,
    cast(livro_id as integer) as livro_id,
    upper(trim(formato)) as formato,
    cast(quantidade as integer) as quantidade,
    cast(preco_unitario as numeric(10, 2)) as preco_unitario,
    cast(valor_total as numeric(10, 2)) as valor_total,
    upper(trim(pagamento_status)) as pagamento_status,
    upper(trim(aprovacao_humana)) as aprovacao_humana,
    upper(trim(documento_status)) as documento_status,
    cast(criado_em as timestamp) as criado_em

from {{ source('readly_raw', 'vendas') }}
