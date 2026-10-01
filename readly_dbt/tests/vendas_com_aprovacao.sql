select *
from {{ ref('fct_vendas') }}
where pagamento_status <> 'TESTE_APROVADO'
   or aprovacao_humana <> 'APROVADA'
   or documento_status <> 'SIMULADO_APROVADO'
