"""Carga dos CSVs de catálogo, atendimentos e vendas no PostgreSQL.

Na camada raw todas as colunas ficam como texto. As conversões para número,
data e booleano são feitas nos modelos staging do dbt.
"""

import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


RAIZ_PROJETO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROJETO / ".env")

# Arquivo CSV -> tabela raw. A primeira coluna de cada lista é a chave primária.
TABELAS = {
    "catalogo_livros.csv": (
        "raw.catalogo_livros",
        ["produto_id", "livro_id", "saga", "titulo", "volume", "genero", "temas", "ritmo",
         "tom", "publico_alvo", "formato", "preco", "estoque", "disponivel", "atualizado_em"],
    ),
    "atendimentos.csv": (
        "raw.atendimentos",
        ["atendimento_id", "usuario_id", "iniciado_em", "necessidade_declarada", "intencao",
         "para_quem", "genero_desejado", "tom_desejado", "formato_desejado", "orcamento",
         "livro_procurado_id", "livro_recomendado_id", "formato_recomendado", "preco_informado",
         "estoque_informado", "pontuacao_recomendacao", "recomendacao_aceita", "etapa_final",
         "resultado", "motivo_abandono", "avaliacao", "custo_ia_eur"],
    ),
    "vendas.csv": (
        "raw.vendas",
        ["pedido_id", "atendimento_id", "usuario_id", "produto_id", "livro_id", "formato",
         "quantidade", "preco_unitario", "valor_total", "pagamento_status", "aprovacao_humana",
         "documento_status", "criado_em"],
    ),
}


def _configuracao_banco():
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5433")),
        "dbname": os.getenv("POSTGRES_DB", "readly_link"),
        "user": os.getenv("POSTGRES_USER", "readly"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


def _ler_csv(caminho):
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de negócio não encontrado: {caminho}")

    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _comando_criacao(tabela, colunas):
    """Monta o CREATE TABLE com todas as colunas como texto.

    Exemplo: create table raw.vendas (pedido_id text primary key, ...)
    """
    definicoes = [f"{colunas[0]} text primary key"]
    for coluna in colunas[1:]:
        definicoes.append(f"{coluna} text")
    definicoes.append("carregado_em timestamptz not null default current_timestamp")

    return f"create table {tabela} ({', '.join(definicoes)});"


def carregar_dados_negocio(diretorio="data"):
    """Recria as três tabelas raw e carrega os CSVs."""

    pasta = Path(diretorio)
    totais = {}

    with psycopg.connect(**_configuracao_banco()) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("create schema if not exists raw;")

            for arquivo, (tabela, colunas) in TABELAS.items():
                registros = _ler_csv(pasta / arquivo)

                # A tabela é recriada a cada carga. Assim, se o CSV ganhar uma
                # coluna nova, o banco não fica com a estrutura antiga.
                # O cascade apaga também as views do dbt que dependem dela;
                # o próximo "dbt build" cria tudo de novo.
                cursor.execute(f"drop table if exists {tabela} cascade;")
                cursor.execute(_comando_criacao(tabela, colunas))

                # insert into raw.vendas (pedido_id, ...) values (%(pedido_id)s, ...)
                nomes = ", ".join(colunas)
                marcadores = ", ".join(f"%({coluna})s" for coluna in colunas)
                cursor.executemany(
                    f"insert into {tabela} ({nomes}) values ({marcadores});",
                    registros,
                )

                totais[tabela] = len(registros)

    resumo = ", ".join(f"{quantidade} em {tabela}" for tabela, quantidade in totais.items())
    print(f"Dados de negócio carregados: {resumo}.")
    return totais
