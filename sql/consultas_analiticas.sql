-- Consultas prontas para responder às perguntas do cliente.
-- Execute depois de: python src/main.py && dbt build

-- 1. Por que os clientes encerraram o atendimento sem comprar? (com evidência)
select
    motivo_abandono,
    etapa_onde_parou,
    atendimentos,
    percentual_abandonos,
    evidencia_preco_acima_orcamento,
    evidencia_procurado_indisponivel,
    evidencia_continuacao_nao_oferecida,
    evidencia_recomendacao_inadequada,
    casos_presente
from analytics.mart_motivos_abandono
order by atendimentos desc;

-- 2. Até onde a venda chega?
select etapa, quantidade, percentual_inicial, perdidos_nesta_etapa
from analytics.mart_funil_vendas
order by ordem;

-- 3. O que estava ruim e o que a solução mudou?
select indicador, base, antes_percentual, depois_percentual, ganho_pontos_percentuais
from analytics.mart_antes_depois
order by ordem;

-- 4. Quantos casos receberam solução automática e quantos vão para uma pessoa?
select
    motivo_abandono,
    casos_encontrados,
    casos_com_solucao,
    casos_para_revisao_humana,
    cobertura_percentual,
    acoes_utilizadas
from analytics.mart_resultado_solucoes
order by casos_encontrados desc;

-- 5. Qual ação executar em cada atendimento perdido (revisão humana primeiro)?
select
    atendimento_id,
    motivo_abandono,
    acao_gerada,
    titulo_solucao,
    formato_solucao,
    preco_solucao,
    orcamento,
    status_solucao,
    motivo_revisao,
    justificativa_solucao
from analytics.mart_solucoes_atendimento
order by status_solucao = 'REVISAO_HUMANA' desc, motivo_abandono, atendimento_id;

-- 6. Nova recomendação de um atendimento, com a pontuação aberta.
-- Troque ATD-001684 pelo atendimento que deseja explicar.
select
    atendimento_id,
    necessidade_declarada,
    para_quem,
    genero_desejado,
    tom_desejado,
    formato_desejado,
    orcamento,
    titulo_antes,
    preco_antes,
    titulo,
    saga,
    volume,
    formato,
    preco,
    case when estoque_ilimitado then 'Digital · sempre disponível'
         else estoque::text || ' unidades' end as estoque,
    pontuacao,
    pontos_livro_procurado,
    pontos_genero,
    pontos_tom,
    pontos_formato,
    pontos_preco,
    justificativa
from analytics.mart_recomendacao_atendimento
where atendimento_id = 'ATD-001684';

-- 7. Recomendação de catálogo por cliente (só histórico, sem conversa).
select
    usuarios.nome_completo,
    recomendacoes.genero_preferido,
    recomendacoes.tom_preferido,
    recomendacoes.formato_preferido,
    recomendacoes.titulo,
    recomendacoes.saga,
    recomendacoes.volume,
    recomendacoes.preco,
    recomendacoes.pontuacao,
    recomendacoes.motivo
from analytics.mart_recomendacoes_usuario as recomendacoes
join analytics.dim_usuarios as usuarios using (usuario_id)
order by recomendacoes.pontuacao desc, usuarios.nome_completo
limit 20;

-- 8. Auditar uma conversa e a venda correspondente.
select
    atendimentos.*,
    vendas.pedido_id,
    vendas.valor_total,
    vendas.pagamento_status,
    vendas.aprovacao_humana
from analytics.fct_atendimentos as atendimentos
left join analytics.fct_vendas as vendas using (atendimento_id)
where atendimentos.atendimento_id = 'ATD-000001';
