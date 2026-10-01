"""Consulta os marts do dbt e grava os resultados num arquivo JSON.

O JSON é lido pela página visual (readly_dbt/site) e pelo script
escrever_respostas.py, que escreve o texto das 23 respostas.
"""

import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVO_JSON = RAIZ_PROJETO / "readly_dbt" / "target" / "business_metrics.json"
load_dotenv(RAIZ_PROJETO / ".env")


def conectar():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        dbname=os.getenv("POSTGRES_DB", "readly_link"),
        user=os.getenv("POSTGRES_USER", "readly"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        row_factory=dict_row,  # cada linha vem como dicionário
    )


def converter(valor):
    """O PostgreSQL devolve Decimal e datas; o JSON só aceita número e texto."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


def buscar(cursor, consulta):
    """Executa a consulta e devolve uma lista de dicionários."""
    cursor.execute(consulta)
    linhas = []
    for linha in cursor.fetchall():
        linhas.append({coluna: converter(valor) for coluna, valor in linha.items()})
    return linhas


def buscar_uma(cursor, consulta):
    """Executa a consulta e devolve só a primeira linha."""
    linhas = buscar(cursor, consulta)
    return linhas[0] if linhas else {}


# ------------------------------------------------------------------ consultas

CONSULTA_TOTAIS = """
    select
        (select count(*) from analytics.dim_usuarios) as usuarios,
        (select count(*) from analytics.int_perfil_leitura_usuario) as perfis,
        (select count(*) from analytics.dim_livros) as livros,
        (select count(*) from analytics.dim_produtos) as ofertas,
        (select count(*) from analytics.dim_produtos where formato = 'FISICO') as fisicos,
        (select count(*) from analytics.dim_produtos
          where formato = 'FISICO' and not disponivel) as fisicos_sem_estoque,
        (select count(*) from analytics.fct_vendas) as vendas,
        (select count(*) from analytics.fct_atendimentos
          where resultado = 'SEM_COMPRA') as sem_compra
"""

# Contagens usadas no texto das respostas sobre as soluções.
CONSULTA_CONTAGENS_SOLUCOES = """
    select
        sum(case when solucao_gerada then 1 else 0 end) as automaticas,
        sum(case when status_solucao = 'ACAO_PRONTA' then 1 else 0 end) as acao_pronta,
        sum(case when status_solucao = 'ALTERNATIVA_ENCONTRADA' then 1 else 0 end) as alternativa,
        sum(case when status_solucao = 'REVISAO_HUMANA' then 1 else 0 end) as revisao_humana,

        sum(case when acao_gerada = 'RETOMAR_CHECKOUT' then 1 else 0 end) as checkout_mesmo_livro,
        sum(case when acao_gerada = 'RETOMAR_CHECKOUT_COM_OPCAO_ADEQUADA'
                  and solucao_gerada then 1 else 0 end) as checkout_outro_livro,

        sum(case when motivo_abandono = 'apenas_pesquisando'
                  and status_solucao = 'ACAO_PRONTA' then 1 else 0 end) as pesquisando_mesmo_livro,
        sum(case when motivo_abandono = 'apenas_pesquisando'
                  and status_solucao = 'ALTERNATIVA_ENCONTRADA' then 1 else 0 end) as pesquisando_outro_livro,

        sum(case when acao_gerada = 'OFERECER_PROXIMO_VOLUME'
                  and solucao_gerada then 1 else 0 end) as continuacao_proximo_volume,
        sum(case when acao_gerada = 'OFERECER_SAGA_SEMELHANTE'
                  and solucao_gerada then 1 else 0 end) as continuacao_saga_semelhante,
        sum(case when motivo_revisao = 'O próximo volume não cabe no orçamento em nenhum formato'
                  then 1 else 0 end) as continuacao_revisao_orcamento,
        sum(case when motivo_revisao = 'Não há saga semelhante adequada disponível'
                  then 1 else 0 end) as continuacao_revisao_sem_saga,

        sum(case when acao_gerada = 'OFERECER_OUTRO_FORMATO_E_AVISAR_REPOSICAO'
                  then 1 else 0 end) as estoque_outro_formato,
        sum(case when acao_gerada = 'OFERECER_SIMILAR_E_AVISAR_REPOSICAO'
                  and solucao_gerada then 1 else 0 end) as estoque_similar
    from analytics.mart_solucoes_atendimento
"""

CONSULTA_REVISAO = """
    select motivo_revisao, count(*) as casos
    from analytics.mart_solucoes_atendimento
    where not solucao_gerada
    group by motivo_revisao
    order by casos desc, motivo_revisao
"""

# Um exemplo de solução para cada motivo (o de maior pontuação).
CONSULTA_EXEMPLOS_SOLUCOES = """
    select distinct on (motivo_abandono)
        motivo_abandono,
        atendimento_id,
        acao_gerada,
        orcamento,
        titulo_recomendado,
        preco_informado,
        titulo_procurado,
        titulo_solucao,
        formato_solucao,
        preco_solucao,
        pontuacao_solucao,
        status_solucao
    from analytics.mart_solucoes_atendimento
    where solucao_gerada
    order by
        motivo_abandono,
        status_solucao = 'ALTERNATIVA_ENCONTRADA' desc,
        pontuacao_solucao desc,
        atendimento_id
"""

# Exemplo explicável: cliente que não encontrou a continuação da saga e que,
# com as regras novas, recebe o próximo volume no formato que pediu.
CONSULTA_EXEMPLO = """
    select
        novo.atendimento_id,
        usuarios.nome_completo,
        novo.necessidade_declarada,
        novo.para_quem,
        novo.genero_desejado,
        novo.tom_desejado,
        novo.formato_desejado,
        novo.orcamento,
        perfil.genero_preferido,
        perfil.formato_preferido,
        perfil.livros_lidos,
        novo.ultima_saga,
        novo.ultimo_volume_lido,
        novo.titulo_antes,
        livro_antigo.volume as volume_antes,
        novo.preco_antes,
        novo.titulo,
        novo.saga,
        novo.volume,
        novo.formato,
        novo.preco,
        novo.estoque,
        novo.estoque_ilimitado,
        novo.pontuacao,
        novo.pontos_livro_procurado,
        novo.pontos_genero,
        novo.pontos_tom,
        novo.pontos_formato,
        novo.pontos_preco,
        novo.justificativa
    from analytics.mart_recomendacao_atendimento as novo
    join analytics.dim_usuarios as usuarios
        on usuarios.usuario_id = novo.usuario_id
    join analytics.int_perfil_leitura_usuario as perfil
        on perfil.usuario_id = novo.usuario_id
    join analytics.int_contexto_atendimento as contexto
        on contexto.atendimento_id = novo.atendimento_id
    join analytics.dim_livros as livro_antigo
        on livro_antigo.livro_id = contexto.livro_recomendado_id
    where novo.intencao = 'continuacao_de_saga'
      and novo.motivo_abandono = 'nao_encontrou_continuacao'
      and novo.livro_id = novo.livro_procurado_id
      and novo.formato = novo.formato_desejado
      and novo.para_quem = 'PROPRIO'
    order by novo.pontuacao desc, novo.atendimento_id
    limit 1
"""


def exportar_metricas():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            dados = {
                "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
                "dados": "Dados fictícios gerados para demonstração",
                "totais": buscar_uma(cursor, CONSULTA_TOTAIS),
                "qualidade": buscar_uma(cursor, "select * from analytics.mart_qualidade_operacional"),
                "motivos_abandono": buscar(
                    cursor, "select * from analytics.mart_motivos_abandono order by atendimentos desc"
                ),
                "funil": buscar(cursor, "select * from analytics.mart_funil_vendas order by ordem"),
                "antes_depois": buscar(cursor, "select * from analytics.mart_antes_depois order by ordem"),
                "resultados_solucoes": buscar(
                    cursor,
                    "select * from analytics.mart_resultado_solucoes order by casos_encontrados desc",
                ),
                "contagens_solucoes": buscar_uma(cursor, CONSULTA_CONTAGENS_SOLUCOES),
                "revisao": buscar(cursor, CONSULTA_REVISAO),
                "exemplos_solucoes": buscar(cursor, CONSULTA_EXEMPLOS_SOLUCOES),
                "exemplo": buscar_uma(cursor, CONSULTA_EXEMPLO),
            }

    ARQUIVO_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Métricas de negócio exportadas para: {ARQUIVO_JSON}")


if __name__ == "__main__":
    exportar_metricas()
