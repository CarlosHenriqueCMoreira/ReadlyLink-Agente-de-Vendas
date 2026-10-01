-- POR QUE O ATENDIMENTO TERMINOU SEM COMPRA
-- Uma linha por motivo. As colunas "evidencia_" contam em quantos casos a
-- causa aparece nos dados. O teste motivos_tem_evidencia exige 100%.

with abandonos as (
    select
        contexto.*,
        candidato.volume_ok as recomendacao_respeitou_saga
    from {{ ref('int_contexto_atendimento') }} as contexto
    join {{ ref('int_candidatos_atendimento') }} as candidato
        on candidato.atendimento_id = contexto.atendimento_id
       and candidato.produto_id = contexto.produto_recomendado_id
    where contexto.resultado = 'SEM_COMPRA'
),

marcados as (
    select
        *,
        preco_informado > orcamento as preco_acima,
        livro_procurado_id is not null and not procurado_disponivel_no_formato as procurado_indisponivel,
        intencao = 'continuacao_de_saga'
            and livro_recomendado_id is distinct from livro_procurado_id as continuacao_nao_oferecida,
        genero_recomendado <> genero_desejado or tom_recomendado <> tom_desejado as gosto_diferente,
        not recomendacao_respeitou_saga as pulou_volume
    from abandonos
)

select
    motivo_abandono,
    min(etapa_final) as etapa_onde_parou,
    count(*) as atendimentos,
    round(100.0 * count(*) / sum(count(*)) over (), 1) as percentual_abandonos,

    sum(case when preco_acima then 1 else 0 end) as evidencia_preco_acima_orcamento,
    sum(case when procurado_indisponivel then 1 else 0 end) as evidencia_procurado_indisponivel,
    sum(case when continuacao_nao_oferecida then 1 else 0 end) as evidencia_continuacao_nao_oferecida,
    sum(case when gosto_diferente then 1 else 0 end) as evidencia_gosto_diferente,
    sum(case when pulou_volume then 1 else 0 end) as evidencia_pula_volume,
    sum(case when gosto_diferente or pulou_volume then 1 else 0 end) as evidencia_recomendacao_inadequada,
    sum(case when para_quem = 'PRESENTE' then 1 else 0 end) as casos_presente,
    round(avg(preco_informado - orcamento), 2) as diferenca_media_preco_orcamento

from marcados
group by motivo_abandono
order by atendimentos desc
