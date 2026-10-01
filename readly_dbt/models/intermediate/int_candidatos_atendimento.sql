{{ config(materialized='table') }}

-- MOTOR DE REGRAS DA NOVA RECOMENDAÇÃO
-- Cruza cada atendimento com cada produto disponível e verifica as regras.
-- Granularidade: uma linha por atendimento x produto (2.400 x ~88 linhas).
-- É uma tabela porque três marts leem este modelo.
--
-- Um livro é ADEQUADO quando:
--   1. está disponível (só entram produtos disponíveis);
--   2. cabe no orçamento;
--   3. o cliente ainda não leu (em presentes o histórico de quem compra não conta);
--   4. respeita a ordem da saga (volume 1 ou o volume anterior já foi lido;
--      em presentes, só volume 1);
--   5. é do gênero pedido.
-- Exceção: se é o livro que o cliente pediu (título específico ou próximo
-- volume da saga), as regras 4 e 5 não se aplicam.

with contexto as (
    select * from {{ ref('int_contexto_atendimento') }}
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

-- Livros que cada usuário já leu.
livros_lidos as (
    select distinct usuario_id, livro_id
    from {{ ref('fct_livros_pegos') }}
),

-- Volumes de cada saga que cada usuário já leu.
volumes_lidos as (
    select distinct usuario_id, saga, volume
    from {{ ref('fct_livros_pegos') }}
),

-- Passo 1: verificar cada regra.
regras as (
    select
        contexto.atendimento_id,
        contexto.usuario_id,
        contexto.intencao,
        contexto.para_quem,
        contexto.orcamento,
        contexto.livro_procurado_id,
        produto.produto_id,
        produto.formato,
        produto.preco,
        produto.estoque,
        produto.estoque_ilimitado,
        produto.livro_id,
        produto.titulo,
        produto.saga,
        produto.volume,
        produto.genero,
        produto.tom,

        produto.preco <= contexto.orcamento as dentro_orcamento,
        produto.genero = contexto.genero_desejado as genero_ok,
        produto.tom = contexto.tom_desejado as tom_ok,
        produto.formato = contexto.formato_desejado as formato_ok,
        produto.livro_id = contexto.livro_procurado_id as e_livro_procurado,

        -- Em presentes, o histórico de quem compra não conta.
        contexto.para_quem = 'PROPRIO' and lido.livro_id is not null as ja_lido,

        case
            when produto.volume = 1 then true
            when contexto.para_quem = 'PRESENTE' then false
            else volume_anterior.volume is not null
        end as volume_ok

    from contexto
    cross join produtos_disponiveis as produto
    left join livros_lidos as lido
        on lido.usuario_id = contexto.usuario_id
       and lido.livro_id = produto.livro_id
    left join volumes_lidos as volume_anterior
        on volume_anterior.usuario_id = contexto.usuario_id
       and volume_anterior.saga = produto.saga
       and volume_anterior.volume = produto.volume - 1
),

-- Passo 2: dar pontos. Total máximo = 100.
-- livro pedido 30, gênero 30, tom 15, formato 15, folga no orçamento até 10.
pontos as (
    select
        *,
        case when genero_ok then 30 else 0 end as pontos_genero,
        case when tom_ok then 15 else 0 end as pontos_tom,
        case when formato_ok then 15 else 0 end as pontos_formato,
        case when e_livro_procurado then 30 else 0 end as pontos_livro_procurado,

        -- Quanto mais barato em relação ao orçamento, mais pontos (0 a 10).
        case
            when dentro_orcamento then round(10 * (orcamento - preco) / orcamento)::integer
            else 0
        end as pontos_preco
    from regras
)

-- Passo 3: juntar tudo e escrever a justificativa.
select
    atendimento_id,
    usuario_id,
    intencao,
    para_quem,
    orcamento,
    livro_procurado_id,
    produto_id,
    formato,
    preco,
    estoque,
    estoque_ilimitado,
    livro_id,
    titulo,
    saga,
    volume,
    genero,
    tom,
    dentro_orcamento,
    genero_ok,
    tom_ok,
    formato_ok,
    e_livro_procurado,
    ja_lido,
    volume_ok,

    not ja_lido
        and dentro_orcamento
        and (e_livro_procurado or (volume_ok and genero_ok)) as adequado,

    pontos_genero,
    pontos_tom,
    pontos_formato,
    pontos_livro_procurado,
    pontos_preco,
    pontos_genero + pontos_tom + pontos_formato + pontos_livro_procurado + pontos_preco
        as pontuacao,

    -- Frase que o vendedor pode ler para o cliente.
    -- concat_ws junta as partes com "; " e ignora as que forem nulas.
    concat_ws(
        '; ',
        case
            when e_livro_procurado and intencao = 'continuacao_de_saga'
                then 'é o próximo volume da saga ' || saga || ' (volume ' || volume || ')'
            when e_livro_procurado and not volume_ok
                then 'é o título que o cliente procurou (avisar que é o volume '
                     || volume || ' da saga ' || saga || ')'
            when e_livro_procurado
                then 'é o título que o cliente procurou'
        end,
        case when genero_ok then 'é do gênero pedido (' || genero || ')' end,
        case when tom_ok then 'tem o tom pedido (' || tom || ')' end,
        case
            when formato_ok then 'está no formato pedido (' || lower(formato) || ')'
            else 'é oferecido em ' || lower(formato)
        end,
        case
            when dentro_orcamento
                then 'cabe no orçamento (' || replace(preco::text, '.', ',')
                     || ' € de ' || replace(orcamento::text, '.', ',') || ' €)'
        end,
        case
            when not e_livro_procurado and volume = 1 then 'começa uma saga do início'
            when not e_livro_procurado and volume_ok
                then 'segue a ordem da saga (o volume anterior já foi lido)'
        end,
        case when para_quem = 'PROPRIO' and not ja_lido then 'o cliente ainda não leu' end
    ) as justificativa

from pontos
