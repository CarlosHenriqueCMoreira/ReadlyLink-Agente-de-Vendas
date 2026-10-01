-- O 9999 do sistema de origem não pode chegar às tabelas analíticas.

select produto_id
from {{ ref('dim_produtos') }}
where (formato = 'DIGITAL' and (estoque is not null or not estoque_ilimitado))
   or (formato = 'FISICO' and (estoque is null or estoque_ilimitado))
