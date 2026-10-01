-- Catálogo descritivo dos livros.
-- Preço, formato e estoque ficam na dimensão de produtos.

select distinct
    livro_id,
    saga,
    titulo,
    volume,
    genero,
    temas,
    ritmo,
    tom,
    publico_alvo

from {{ ref('stg_catalogo_livros') }}
