"""Etapa de carga do ETL da Readly Link."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv


RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env")


def _configuracao_banco() -> dict[str, str | int]:
    """Lê a conexão do PostgreSQL a partir das variáveis do arquivo .env."""

    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "dbname": os.getenv("POSTGRES_DB", "readly_link"),
        "user": os.getenv("POSTGRES_USER", "readly"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


def carregar(registros: list[dict[str, Any]]) -> int:
    """Substitui a carga raw pelo conteúdo transformado nesta execução.

    O TRUNCATE e os INSERTs participam da mesma transação. Se algum INSERT
    falhar, o PostgreSQL desfaz toda a carga e mantém a tabela anterior.
    """

    if not registros:
        raise ValueError("Não existem registros para carregar.")

    comando_criacao = """
        create schema if not exists raw;

        create table if not exists raw.usuarios_csv (
            registro_hash          text primary key,
            numero_linha_fonte     integer not null,
            usuario_ref            text not null,
            nome_completo          text not null,
            idade                  text,
            tipo_documento         text,
            documento              text not null,
            livros_pegos           text not null,
            arquivo_origem         text not null default 'usuarios_readly.csv',
            carregado_em           timestamptz not null default current_timestamp
        );
    """

    comando_insercao = """
        insert into raw.usuarios_csv (
            registro_hash,
            numero_linha_fonte,
            usuario_ref,
            nome_completo,
            idade,
            tipo_documento,
            documento,
            livros_pegos
        )
        values (
            %(registro_hash)s,
            %(_numero_linha_fonte)s,
            %(usuario_ref)s,
            %(nome_completo)s,
            %(idade)s,
            %(tipo_documento)s,
            %(documento)s,
            %(livros_pegos)s
        );
    """

    # Os gerenciadores de contexto fecham cursor e conexão automaticamente.
    with psycopg.connect(**_configuracao_banco()) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(comando_criacao)
            cursor.execute("truncate table raw.usuarios_csv;")
            cursor.executemany(comando_insercao, registros)

    quantidade = len(registros)
    print(f"ETL concluído: {quantidade} usuários carregados em raw.usuarios_csv.")
    return quantidade
