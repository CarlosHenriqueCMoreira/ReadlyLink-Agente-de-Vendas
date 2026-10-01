-- RECOMENDAÇÃO DE CATÁLOGO POR USUÁRIO
-- Usa só o histórico (não há conversa, por isso não há orçamento).
-- Regras: disponível, ainda não lido e sem pular volume de saga.
-- Pontos: gênero preferido 40, tom preferido 20, formato preferido 15,
-- continuar uma saga já começada 25.

with perfil as (
    select * from {{ ref('int_perfil_leitura_usuario') }}
),

livros_lidos as (
    select distinct usuario_id, livro_id
    from {{ ref('fct_livros_pegos') }}
),

volumes_lidos as (
    select distinct usuario_id, saga, volume
    from {{ ref('fct_livros_pegos') }}
),

produtos_disponiveis as (
    select
        produtos.produto_id,
        produtos.formato,
        produtos.preco,
        produtos.estoque,
        produtos.estoque_ilimitado,
        livros.livro_id,
        livros.titulo,
        livros.saga,
        livros.volume,
        livros.genero,
        livros.tom
    from {{ ref('dim_produtos') }} as produtos
    join {{ ref('dim_livros') }} as livros
        on produtos.livro_id = livros.livro_id
    where produtos.disponivel
),

candidatos as (
    select
        perfil.usuario_id,
        perfil.genero_preferido,
        perfil.tom_preferido,
        perfil.formato_preferido,
        produto.*,
        produto.genero = perfil.genero_preferido as genero_ok,
        produto.tom = perfil.tom_preferido as tom_ok,
        produto.formato = perfil.formato_preferido as formato_ok,
        produto.volume > 1 as continua_saga
    from perfil
    cross join produtos_disponiveis as produto
    left join livros_lidos as lido
        on lido.usuario_id = perfil.usuario_id
       and lido.livro_id = produto.livro_id
    left join volumes_lidos as volume_anterior
        on volume_anterior.usuario_id = perfil.usuario_id
       and volume_anterior.saga = produto.saga
       and volume_anterior.volume = produto.volume - 1
    where lido.livro_id is null                                   -- ainda não leu
      and (produto.volume = 1 or volume_anterior.volume is not null) -- não pula volume
),

pontuados as (
    select
        *,
        case when genero_ok then 40 else 0 end
        + case when tom_ok then 20 else 0 end
        + case when formato_ok then 15 else 0 end
        + case when continua_saga then 25 else 0 end as pontuacao
    from candidatos
),

ranking as (
    select
        *,
        row_number() over (
            partition by usuario_id
            order by pontuacao desc, preco, produto_id
        ) as posicao
    from pontuados
)

select
    usuario_id,
    genero_preferido,
    tom_preferido,
    formato_preferido,
    livro_id,
    produto_id,
    titulo,
    saga,
    volume,
    genero,
    formato,
    preco,
    estoque,
    estoque_ilimitado,
    pontuacao,
    concat_ws(
        '; ',
        case
            when continua_saga then 'continua a saga ' || saga || ' (volume ' || volume || ')'
            else 'começa a saga ' || saga
        end,
        case when genero_ok then 'gênero mais lido (' || genero || ')' end,
        case when tom_ok then 'tom preferido (' || tom || ')' end,
        case when formato_ok then 'formato preferido (' || lower(formato) || ')' end,
        'ainda não lido'
    ) as motivo

from ranking
where posicao = 1
