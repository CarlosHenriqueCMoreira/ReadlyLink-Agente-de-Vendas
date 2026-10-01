-- SOLUÇÃO PARA CADA ATENDIMENTO PERDIDO
-- Uma linha por atendimento que terminou sem compra.
--
-- Como funciona:
--   1. pega os livros do motor de regras (int_candidatos_atendimento);
--   2. aplica a regra de cada motivo de abandono (quais livros servem);
--   3. escolhe o melhor livro (prioridade, pontuação, preço);
--   4. se nenhum livro serve, o caso vai para revisão humana.
-- A ação gerada NÃO é contada como venda recuperada.

with abandonos as (
    select *
    from {{ ref('int_contexto_atendimento') }}
    where resultado = 'SEM_COMPRA'
),

candidatos as (
    select
        abandonos.motivo_abandono,
        candidato.*,

        -- Mesmo livro que o agente antigo tinha recomendado?
        candidato.produto_id = abandonos.produto_recomendado_id as e_produto_recomendado,
        candidato.livro_id = abandonos.livro_recomendado_id as e_livro_recomendado,
        candidato.saga <> abandonos.saga_recomendada as outra_saga,

        -- Informações para quem não encontrou a continuação.
        abandonos.livro_procurado_id is null as saga_ja_concluida,
        candidato.saga <> abandonos.ultima_saga as fora_da_ultima_saga,
        candidato.genero = abandonos.genero_ultima_saga as mesmo_genero_da_saga,
        candidato.tom = abandonos.tom_ultima_saga as mesmo_tom_da_saga,

        -- Informação para quem procurou um livro sem estoque.
        candidato.genero = abandonos.genero_procurado as mesmo_genero_do_procurado

    from abandonos
    join {{ ref('int_candidatos_atendimento') }} as candidato
        on candidato.atendimento_id = abandonos.atendimento_id
),

-- Passo 2: regra de cada motivo.
elegiveis as (
    select *
    from candidatos
    where
        -- Preço, checkout e pesquisa: qualquer livro adequado.
        (motivo_abandono in ('preco_acima_do_orcamento', 'abandono_no_checkout', 'apenas_pesquisando')
            and adequado)

        -- Não combinou: um livro adequado diferente do que foi recusado.
        or (motivo_abandono = 'recomendacao_nao_combinou'
            and adequado
            and not e_livro_recomendado)

        -- Continuação, quando existe próximo volume: o próximo volume no orçamento.
        or (motivo_abandono = 'nao_encontrou_continuacao'
            and not saga_ja_concluida
            and e_livro_procurado
            and dentro_orcamento
            and not ja_lido)

        -- Continuação, quando a saga já acabou: volume 1 de outra saga
        -- com o mesmo gênero ou o mesmo tom.
        or (motivo_abandono = 'nao_encontrou_continuacao'
            and saga_ja_concluida
            and not ja_lido
            and dentro_orcamento
            and volume = 1
            and fora_da_ultima_saga
            and (mesmo_genero_da_saga or mesmo_tom_da_saga))

        -- Sem estoque: o mesmo livro em outro formato, ou um adequado do mesmo gênero.
        or (motivo_abandono = 'livro_procurado_sem_estoque'
            and ((e_livro_procurado and dentro_orcamento)
                 or (adequado and mesmo_genero_do_procurado)))
),

-- Passo 3: escolher o melhor livro de cada atendimento.
-- Prioridade 0 = o livro mais óbvio para aquele motivo.
ranking as (
    select
        *,
        case
            when motivo_abandono in ('abandono_no_checkout', 'apenas_pesquisando')
                 and e_produto_recomendado then 0
            when motivo_abandono = 'preco_acima_do_orcamento' and e_livro_recomendado then 0
            when e_livro_procurado then 0
            when motivo_abandono = 'recomendacao_nao_combinou' and outra_saga then 1
            when motivo_abandono = 'nao_encontrou_continuacao' and mesmo_genero_da_saga then 1
            else 2
        end as prioridade
    from elegiveis
),

melhor_livro as (
    select
        *,
        row_number() over (
            partition by atendimento_id
            order by prioridade, pontuacao desc, preco, produto_id
        ) as posicao
    from ranking
)

-- Passo 4: montar a ação de cada atendimento.
select
    abandonos.atendimento_id,
    abandonos.usuario_id,
    abandonos.intencao,
    abandonos.para_quem,
    abandonos.motivo_abandono,
    abandonos.etapa_final,
    abandonos.orcamento,
    abandonos.genero_desejado,
    abandonos.formato_desejado,

    -- O que tinha sido oferecido antes
    abandonos.titulo_recomendado,
    abandonos.formato_recomendado,
    abandonos.preco_informado,

    -- O que o cliente procurava
    abandonos.livro_procurado_id,
    abandonos.titulo_procurado,
    abandonos.saga_concluida,

    case
        when abandonos.motivo_abandono = 'preco_acima_do_orcamento'
            then 'OFERECER_OPCAO_NO_ORCAMENTO'
        when abandonos.motivo_abandono = 'recomendacao_nao_combinou'
            then 'REFAZER_RECOMENDACAO'
        when abandonos.motivo_abandono = 'abandono_no_checkout' and melhor.e_produto_recomendado
            then 'RETOMAR_CHECKOUT'
        when abandonos.motivo_abandono = 'abandono_no_checkout'
            then 'RETOMAR_CHECKOUT_COM_OPCAO_ADEQUADA'
        when abandonos.motivo_abandono = 'apenas_pesquisando'
            then 'SALVAR_LISTA_E_LEMBRAR'
        when abandonos.motivo_abandono = 'nao_encontrou_continuacao'
             and abandonos.livro_procurado_id is null
            then 'OFERECER_SAGA_SEMELHANTE'
        when abandonos.motivo_abandono = 'nao_encontrou_continuacao'
            then 'OFERECER_PROXIMO_VOLUME'
        when abandonos.motivo_abandono = 'livro_procurado_sem_estoque' and melhor.e_livro_procurado
            then 'OFERECER_OUTRO_FORMATO_E_AVISAR_REPOSICAO'
        when abandonos.motivo_abandono = 'livro_procurado_sem_estoque'
            then 'OFERECER_SIMILAR_E_AVISAR_REPOSICAO'
    end as acao_gerada,

    melhor.produto_id as produto_solucao_id,
    melhor.titulo as titulo_solucao,
    melhor.saga as saga_solucao,
    melhor.volume as volume_solucao,
    melhor.formato as formato_solucao,
    melhor.preco as preco_solucao,
    melhor.estoque as estoque_solucao,
    melhor.estoque_ilimitado as estoque_ilimitado_solucao,
    melhor.pontuacao as pontuacao_solucao,
    melhor.justificativa as justificativa_solucao,

    case
        when melhor.produto_id is null then 'REVISAO_HUMANA'
        when melhor.e_produto_recomendado then 'ACAO_PRONTA'
        else 'ALTERNATIVA_ENCONTRADA'
    end as status_solucao,

    case
        when melhor.produto_id is not null then null
        when abandonos.motivo_abandono = 'nao_encontrou_continuacao'
             and abandonos.livro_procurado_id is not null
            then 'O próximo volume não cabe no orçamento em nenhum formato'
        when abandonos.motivo_abandono = 'nao_encontrou_continuacao'
            then 'Não há saga semelhante adequada disponível'
        when abandonos.motivo_abandono = 'preco_acima_do_orcamento'
            then 'Nenhum livro adequado cabe no orçamento declarado'
        else 'Nenhuma alternativa cumpre todas as regras'
    end as motivo_revisao,

    melhor.produto_id is not null as solucao_gerada

from abandonos
left join melhor_livro as melhor
    on melhor.atendimento_id = abandonos.atendimento_id
   and melhor.posicao = 1
