-- Converte os dados da conversa para tipos próprios de análise.
-- Os campos de recomendação descrevem o que o agente ANTIGO ofereceu.

select
    trim(atendimento_id) as atendimento_id,
    cast(usuario_id as integer) as usuario_id,
    cast(iniciado_em as timestamp) as iniciado_em,
    trim(necessidade_declarada) as necessidade_declarada,
    trim(intencao) as intencao,
    upper(trim(para_quem)) as para_quem,
    trim(genero_desejado) as genero_desejado,
    trim(tom_desejado) as tom_desejado,
    upper(trim(formato_desejado)) as formato_desejado,
    cast(orcamento as numeric(10, 2)) as orcamento,
    cast(nullif(trim(livro_procurado_id), '') as integer) as livro_procurado_id,
    cast(livro_recomendado_id as integer) as livro_recomendado_id,
    upper(trim(formato_recomendado)) as formato_recomendado,
    trim(livro_recomendado_id) || '-' || upper(trim(formato_recomendado))
        as produto_recomendado_id,
    cast(preco_informado as numeric(10, 2)) as preco_informado,

    -- 9999 no digital significa "ilimitado" e não entra como número.
    case
        when upper(trim(formato_recomendado)) = 'DIGITAL' then null
        else cast(estoque_informado as integer)
    end as estoque_informado,

    cast(pontuacao_recomendacao as integer) as pontuacao_recomendacao,
    upper(trim(recomendacao_aceita)) = 'SIM' as recomendacao_aceita,
    upper(trim(etapa_final)) as etapa_final,
    upper(trim(resultado)) as resultado,
    nullif(trim(motivo_abandono), '') as motivo_abandono,
    cast(avaliacao as integer) as avaliacao,
    cast(custo_ia_eur as numeric(10, 4)) as custo_ia_eur

from {{ source('readly_raw', 'atendimentos') }}
