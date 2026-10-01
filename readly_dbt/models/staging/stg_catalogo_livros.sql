-- Padroniza o catálogo comercial usado para consultar preço e estoque.
-- Uma linha representa um produto: um livro (obra) num formato.

select
    trim(produto_id) as produto_id,
    cast(livro_id as integer) as livro_id,
    trim(saga) as saga,
    trim(titulo) as titulo,
    cast(volume as integer) as volume,
    trim(genero) as genero,
    trim(temas) as temas,
    trim(ritmo) as ritmo,
    trim(tom) as tom,
    trim(publico_alvo) as publico_alvo,
    upper(trim(formato)) as formato,
    cast(preco as numeric(10, 2)) as preco,

    -- O sistema de origem grava 9999 para dizer "ilimitado" no digital.
    -- Esse número não é estoque real, por isso vira nulo aqui.
    case
        when upper(trim(formato)) = 'DIGITAL' then null
        else cast(estoque as integer)
    end as estoque,
    upper(trim(formato)) = 'DIGITAL' as estoque_ilimitado,

    upper(trim(disponivel)) = 'SIM' as disponivel,
    cast(atualizado_em as timestamp) as atualizado_em

from {{ source('readly_raw', 'catalogo_livros') }}
