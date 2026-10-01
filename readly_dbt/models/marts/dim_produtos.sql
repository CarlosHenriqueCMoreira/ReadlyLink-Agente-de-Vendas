-- Oferta comercial consultada pelo agente antes de informar preço e estoque.
-- estoque fica nulo no digital, que é sempre disponível (estoque_ilimitado).

select
    produto_id,
    livro_id,
    formato,
    preco,
    estoque,
    estoque_ilimitado,
    disponivel,
    atualizado_em

from {{ ref('stg_catalogo_livros') }}
