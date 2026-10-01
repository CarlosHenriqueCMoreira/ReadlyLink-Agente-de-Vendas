"""Etapa de transformação técnica do ETL da Readly Link.

A transformação desta camada prepara os registros para a área raw do banco.
As regras de negócio e a modelagem analítica ficam no dbt.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


CAMPOS_DA_FONTE = (
    "usuario_ref",
    "nome_completo",
    "idade",
    "tipo_documento",
    "documento",
    "livros_pegos",
)


def _limpar_texto(valor: str | None) -> str | None:
    """Remove espaços nas extremidades e converte texto vazio em nulo."""

    if valor is None:
        return None

    texto = valor.strip()
    return texto or None


def transformar(
    registros: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Aplica limpeza técnica sem apagar as irregularidades úteis ao dbt.

    O CSV continua com idade e identificador em formato textual. Assim, o dbt
    ainda precisa normalizar esses campos e separar os livros da coluna
    desnormalizada.
    """

    if not registros:
        raise ValueError("Não existem registros para transformar.")

    registros_tratados: list[dict[str, Any]] = []

    for registro in registros:
        numero_linha = registro.get("_numero_linha_fonte", "?")

        # Mantém somente as colunas esperadas e remove espaços nas extremidades.
        tratado = {
            campo: _limpar_texto(registro.get(campo))
            for campo in CAMPOS_DA_FONTE
        }

        # Estes campos identificam o usuário e o conteúdo que será modelado.
        campos_obrigatorios = ("usuario_ref", "nome_completo", "documento", "livros_pegos")
        campos_vazios = [
            campo for campo in campos_obrigatorios if tratado[campo] is None
        ]

        if campos_vazios:
            nomes = ", ".join(campos_vazios)
            raise ValueError(
                f"Linha {numero_linha}: campos obrigatórios vazios: {nomes}."
            )

        try:
            tratado["_numero_linha_fonte"] = int(numero_linha)
        except (TypeError, ValueError) as erro:
            raise ValueError(
                f"Número de linha de origem inválido: {numero_linha!r}."
            ) from erro

        # O hash permite identificar exatamente o conteúdo recebido da fonte.
        conteudo_hash = json.dumps(
            tratado,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        tratado["registro_hash"] = hashlib.sha256(
            conteudo_hash.encode("utf-8")
        ).hexdigest()

        registros_tratados.append(tratado)

    return registros_tratados
