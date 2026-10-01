-- CAMADA STAGING
-- Esta camada limpa os campos recebidos da tabela raw.
-- Ela ainda mantém uma linha para cada usuário.

with fonte as (
    -- Busca os dados que o ETL em Python carregou no PostgreSQL.
    select *
    from {{ source('readly_raw', 'usuarios_csv') }}
)

select
    -- "USR-000001" e "1" passam a representar o mesmo tipo de ID: o número 1.
    cast(
        nullif(regexp_replace(usuario_ref, '[^0-9]', '', 'g'), '')
        as integer
    ) as usuario_id,

    -- Remove espaços repetidos e padroniza o nome como "Carlos Moreira".
    initcap(
        lower(regexp_replace(trim(nome_completo), '\s+', ' ', 'g'))
    ) as nome_completo,

    -- Remove textos como "anos" e converte a idade para número inteiro.
    cast(
        nullif(regexp_replace(idade, '[^0-9]', '', 'g'), '')
        as integer
    ) as idade,

    -- Converte "cpf", "Cpf" ou "rg" para "CPF" e "RG".
    upper(trim(tipo_documento)) as tipo_documento,

    -- Remove espaços e padroniza letras do documento.
    upper(trim(documento)) as documento,

    -- Esta coluna continua agrupada. O próximo modelo separará os livros.
    livros_pegos,

    -- Campos usados para rastrear o registro até o CSV original.
    registro_hash,
    numero_linha_fonte,
    arquivo_origem,
    carregado_em

from fonte
