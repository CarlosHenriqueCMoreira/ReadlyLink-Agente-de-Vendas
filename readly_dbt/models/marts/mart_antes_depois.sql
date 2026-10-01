-- O QUE ESTAVA RUIM E O QUE A SOLUÇÃO MUDOU
-- Compara, nos mesmos atendimentos, a recomendação do agente antigo (antes)
-- com a recomendação das regras novas (depois).
-- Mede o cumprimento das regras, não vendas: a venda só pode ser medida
-- quando o novo atendimento estiver em produção.

with candidatos as (
    select * from {{ ref('int_candidatos_atendimento') }}
),

-- Atendimentos em que o livro pedido estava disponível, cabia no orçamento
-- e ainda não tinha sido lido. Só nesses casos é justo cobrar que ele seja oferecido.
procurado_possivel as (
    select distinct atendimento_id
    from candidatos
    where e_livro_procurado
      and dentro_orcamento
      and not ja_lido
),

-- Regras cumpridas pela recomendação ANTIGA.
antes as (
    select
        contexto.atendimento_id,
        contexto.intencao,
        contexto.para_quem,
        contexto.livro_procurado_id,
        possivel.atendimento_id is not null as procurado_possivel,
        candidatos.livro_id,
        candidatos.dentro_orcamento,
        candidatos.genero_ok,
        candidatos.tom_ok,
        candidatos.volume_ok,
        candidatos.adequado
    from {{ ref('int_contexto_atendimento') }} as contexto
    join candidatos
        on candidatos.atendimento_id = contexto.atendimento_id
       and candidatos.produto_id = contexto.produto_recomendado_id
    left join procurado_possivel as possivel
        on possivel.atendimento_id = contexto.atendimento_id
),

-- Regras cumpridas pela recomendação NOVA.
-- Se não houve recomendação nova (caso para uma pessoa), conta como "não cumpriu".
depois as (
    select
        novo.atendimento_id,
        novo.livro_id,
        coalesce(candidatos.dentro_orcamento, false) as dentro_orcamento,
        coalesce(candidatos.genero_ok, false) as genero_ok,
        coalesce(candidatos.tom_ok, false) as tom_ok,
        coalesce(candidatos.volume_ok, false) as volume_ok,
        coalesce(candidatos.adequado, false) as adequado
    from {{ ref('mart_recomendacao_atendimento') }} as novo
    left join candidatos
        on candidatos.atendimento_id = novo.atendimento_id
       and candidatos.produto_id = novo.produto_id
),

base as (
    select
        antes.*,
        depois.livro_id as livro_id_depois,
        depois.dentro_orcamento as dentro_orcamento_depois,
        depois.genero_ok as genero_ok_depois,
        depois.tom_ok as tom_ok_depois,
        depois.volume_ok as volume_ok_depois,
        depois.adequado as adequado_depois
    from antes
    join depois
        on depois.atendimento_id = antes.atendimento_id
),

-- Um bloco por indicador. "sum(case when ... then 1 else 0 end)" conta as linhas que cumprem a regra.
indicadores as (
    select
        1 as ordem,
        'Recomendação cabe no orçamento' as indicador,
        count(*) as base,
        sum(case when dentro_orcamento then 1 else 0 end) as antes,
        sum(case when dentro_orcamento_depois then 1 else 0 end) as depois
    from base

    union all
    select
        2,
        'Respeita o gênero pedido',
        count(*),
        sum(case when genero_ok then 1 else 0 end),
        sum(case when genero_ok_depois then 1 else 0 end)
    from base

    union all
    select
        3,
        'Respeita o tom de leitura pedido',
        count(*),
        sum(case when tom_ok then 1 else 0 end),
        sum(case when tom_ok_depois then 1 else 0 end)
    from base

    union all
    select
        4,
        'Não pula volume de saga',
        count(*),
        sum(case when volume_ok then 1 else 0 end),
        sum(case when volume_ok_depois then 1 else 0 end)
    from base

    union all
    select
        5,
        'Oferece o próximo volume da saga (quando cabe no orçamento)',
        count(*),
        sum(case when livro_id = livro_procurado_id then 1 else 0 end),
        sum(case when livro_id_depois = livro_procurado_id then 1 else 0 end)
    from base
    where intencao = 'continuacao_de_saga'
      and procurado_possivel

    union all
    select
        6,
        'Oferece o título procurado (disponível e no orçamento)',
        count(*),
        sum(case when livro_id = livro_procurado_id then 1 else 0 end),
        sum(case when livro_id_depois = livro_procurado_id then 1 else 0 end)
    from base
    where intencao = 'titulo_especifico'
      and procurado_possivel

    union all
    select
        7,
        'Presente no gênero de quem vai receber',
        count(*),
        sum(case when genero_ok then 1 else 0 end),
        sum(case when genero_ok_depois then 1 else 0 end)
    from base
    where para_quem = 'PRESENTE'

    union all
    select
        8,
        'Cumpre todas as regras de livro adequado',
        count(*),
        sum(case when adequado then 1 else 0 end),
        sum(case when adequado_depois then 1 else 0 end)
    from base
)

select
    ordem,
    indicador,
    base,
    antes,
    round(100.0 * antes / base, 1) as antes_percentual,
    depois,
    round(100.0 * depois / base, 1) as depois_percentual,
    round(100.0 * (depois - antes) / base, 1) as ganho_pontos_percentuais
from indicadores
order by ordem
