select *
from {{ ref('stg_usuarios') }}
where idade not between 14 and 110
