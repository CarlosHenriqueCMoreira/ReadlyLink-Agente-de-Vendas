-- Uma linha para cada venda concluída no ambiente simulado.

select *
from {{ ref('stg_vendas') }}
