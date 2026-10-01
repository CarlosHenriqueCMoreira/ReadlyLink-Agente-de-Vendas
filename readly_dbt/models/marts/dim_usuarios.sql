-- DIMENSÃO DE USUÁRIOS
-- Uma linha representa um usuário da Readly Link.

select
    usuario_id,
    nome_completo,
    idade,
    tipo_documento,
    documento

from {{ ref('stg_usuarios') }}
