select *
from {{ ref('int_livros_pegos') }}
where quantidade <= 0
