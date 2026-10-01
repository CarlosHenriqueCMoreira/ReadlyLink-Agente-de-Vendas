-- Uma linha para cada conversa iniciada com o agente de vendas.

select *
from {{ ref('stg_atendimentos') }}
