-- TABELA FATO DE RETIRADAS
-- Uma linha representa um livro retirado por um usuário em determinada data.
-- livro_id identifica a obra; edicao_id guarda o ID recebido no CSV.

select
    retirada_id,
    usuario_id,
    livro_id,
    edicao_id,
    saga,
    volume,
    formato,
    quantidade,
    data_retirada

from {{ ref('int_livros_pegos') }}
