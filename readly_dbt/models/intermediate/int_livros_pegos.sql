-- CAMADA INTERMEDIATE
-- Transforma a coluna livros_pegos em várias linhas.
-- A granularidade final é: uma linha para cada livro retirado por um usuário.
--
-- No CSV o mesmo título aparece com dois IDs (um da edição física e outro da
-- digital). O ID recebido fica em edicao_id, e livro_id passa a identificar a
-- obra (saga + volume) do catálogo. Assim "já leu" vale para os dois formatos.

with usuarios as (
    -- Usa os usuários que já foram limpos na camada staging.
    select *
    from {{ ref('stg_usuarios') }}
),

itens as (
    select
        usuarios.usuario_id,
        usuarios.registro_hash,

        -- Guarda a posição original do livro dentro da lista.
        livro_item.posicao_item,

        -- Texto de um único livro, ainda separado pelo caractere "~".
        trim(livro_item.item_livro) as item_livro

    from usuarios

    -- Primeiro separa o texto usando " || ".
    -- Depois o unnest transforma cada elemento da lista em uma nova linha.
    cross join lateral unnest(
        string_to_array(usuarios.livros_pegos, ' || ')
    ) with ordinality as livro_item(item_livro, posicao_item)
),

campos as (
    select
        -- Cria uma chave única para cada retirada.
        md5(
            registro_hash || '|' || cast(posicao_item as text)
        ) as retirada_id,

        usuario_id,

        -- Cada split_part pega uma posição do texto separado por "~".
        cast(
            nullif(split_part(item_livro, '~', 1), '')
            as integer
        ) as edicao_id,

        trim(split_part(item_livro, '~', 2)) as saga,
        trim(split_part(item_livro, '~', 3)) as titulo,

        -- "volume:3" vira o número 3.
        cast(
            nullif(
                regexp_replace(
                    split_part(item_livro, '~', 4),
                    '[^0-9]',
                    '',
                    'g'
                ),
                ''
            )
            as integer
        ) as volume,

        -- Padroniza o formato como FISICO ou DIGITAL.
        upper(trim(split_part(item_livro, '~', 5))) as formato,

        -- "qtd:2" vira o número 2.
        cast(
            nullif(
                regexp_replace(
                    split_part(item_livro, '~', 6),
                    '[^0-9]',
                    '',
                    'g'
                ),
                ''
            )
            as integer
        ) as quantidade,

        -- "data:2026-01-20" vira uma data do PostgreSQL.
        cast(
            nullif(
                regexp_replace(
                    split_part(item_livro, '~', 7),
                    '^data:',
                    ''
                ),
                ''
            )
            as date
        ) as data_retirada

    from itens
),

obras as (
    select distinct livro_id, saga, volume
    from {{ ref('stg_catalogo_livros') }}
)

select
    campos.retirada_id,
    campos.usuario_id,
    obras.livro_id,
    campos.edicao_id,
    campos.saga,
    campos.titulo,
    campos.volume,
    campos.formato,
    campos.quantidade,
    campos.data_retirada

from campos
left join obras
    on campos.saga = obras.saga
   and campos.volume = obras.volume
