-- A pontuação só serve para explicar a escolha se variar entre atendimentos.
-- Falha se houver menos de 10 valores diferentes.

select count(distinct pontuacao) as valores_distintos
from {{ ref('mart_recomendacao_atendimento') }}
having count(distinct pontuacao) < 10
