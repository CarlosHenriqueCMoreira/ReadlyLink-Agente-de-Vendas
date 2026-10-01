select *
from {{ ref('mart_qualidade_operacional') }}
where divergencias_preco > 0
   or recomendacoes_sem_estoque > 0
