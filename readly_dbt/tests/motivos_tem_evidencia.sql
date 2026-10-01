-- Cada motivo de abandono precisa ter a causa visível em 100% dos casos.

select motivo_abandono, atendimentos
from {{ ref('mart_motivos_abandono') }}
where (motivo_abandono = 'preco_acima_do_orcamento'
       and evidencia_preco_acima_orcamento < atendimentos)
   or (motivo_abandono = 'livro_procurado_sem_estoque'
       and evidencia_procurado_indisponivel < atendimentos)
   or (motivo_abandono = 'nao_encontrou_continuacao'
       and evidencia_continuacao_nao_oferecida < atendimentos)
   or (motivo_abandono = 'recomendacao_nao_combinou'
       and evidencia_recomendacao_inadequada < atendimentos)
