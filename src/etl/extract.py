"""Etapa de extração do ETL da Readly Link.

Este módulo abre o CSV entregue pela empresa, valida sua estrutura básica
e devolve os registros sem aplicar regras de limpeza ou transformação.
"""

# Faz o Python tratar as anotações de tipo como texto.
# Isso mantém o arquivo compatível com versões anteriores ao Python 3.10.
from __future__ import annotations

# A biblioteca ``csv`` lê arquivos CSV sem precisar instalar pacotes externos.
import csv

# ``Path`` permite receber caminhos como texto ou como objeto de caminho.
from pathlib import Path


# Define as colunas que precisam existir no arquivo recebido da empresa.
# A extração será interrompida se alguma delas estiver ausente.
COLUNAS_OBRIGATORIAS = {
    "usuario_ref",
    "nome_completo",
    "idade",
    "tipo_documento",
    "documento",
    "livros_pegos",
}


def extrair(caminho_arquivo: str | Path) -> list[dict[str, str]]:
    """Lê o CSV e devolve uma lista com um dicionário para cada usuário.

    Parâmetros
    ----------
    caminho_arquivo:
        Caminho do arquivo CSV que será extraído.

    Retorno
    -------
    list[dict[str, str]]
        Lista de registros. Cada registro usa os nomes das colunas como chaves.

    Exceções
    --------
    FileNotFoundError
        Quando o caminho informado não aponta para um arquivo existente.
    ValueError
        Quando o arquivo não é CSV, está vazio ou possui estrutura inválida.
    """

    # Converte o caminho recebido em um objeto ``Path``.
    caminho = Path(caminho_arquivo)

    # Confere se o caminho realmente aponta para um arquivo.
    if not caminho.is_file():
        # Interrompe a extração com uma mensagem que informa o caminho usado.
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho}")

    # Confere a extensão para evitar a leitura acidental de outro tipo de arquivo.
    if caminho.suffix.lower() != ".csv":
        # Informa que esta etapa aceita somente arquivos CSV.
        raise ValueError(f"Formato inválido. Era esperado um CSV: {caminho}")

    # Abre o arquivo somente para leitura.
    # ``utf-8-sig`` aceita UTF-8 normal e também arquivos com marcador BOM.
    # ``newline=''`` permite que a biblioteca csv controle corretamente as linhas.
    with caminho.open(mode="r", encoding="utf-8-sig", newline="") as arquivo:
        # ``DictReader`` usa o cabeçalho do CSV como chave de cada coluna.
        leitor = csv.DictReader(arquivo)

        # ``fieldnames`` será ``None`` quando o arquivo não tiver cabeçalho.
        if leitor.fieldnames is None:
            # Sem cabeçalho não conseguimos identificar o significado das colunas.
            raise ValueError("O arquivo CSV não possui cabeçalho.")

        # Guarda o cabeçalho numa lista para reutilizá-lo nas validações.
        cabecalho = leitor.fieldnames

        # Compara a quantidade total com a quantidade de nomes únicos.
        # Se forem diferentes, existe pelo menos uma coluna repetida.
        if len(cabecalho) != len(set(cabecalho)):
            # Colunas duplicadas poderiam fazer um valor sobrescrever outro.
            raise ValueError("O arquivo CSV possui nomes de colunas duplicados.")

        # Calcula quais colunas obrigatórias não aparecem no cabeçalho recebido.
        colunas_faltantes = COLUNAS_OBRIGATORIAS.difference(cabecalho)

        # Verifica se o conjunto de colunas faltantes contém algum elemento.
        if colunas_faltantes:
            # Ordena os nomes para produzir uma mensagem previsível e legível.
            faltantes_formatadas = ", ".join(sorted(colunas_faltantes))

            # Interrompe a extração informando exatamente o que está ausente.
            raise ValueError(
                f"O CSV não possui as colunas obrigatórias: {faltantes_formatadas}"
            )

        # Cria a lista que receberá todos os registros extraídos.
        registros = []

        # Percorre as linhas de dados.
        # A contagem começa em 2 porque a linha 1 contém o cabeçalho.
        for numero_linha, registro in enumerate(leitor, start=2):
            # O ``DictReader`` usa a chave ``None`` quando encontra valores extras
            # que não possuem uma coluna correspondente no cabeçalho.
            if None in registro:
                # Interrompe para não aceitar silenciosamente uma linha deformada.
                raise ValueError(
                    f"A linha {numero_linha} possui mais valores que o cabeçalho."
                )

            # Adiciona metadado com a linha original do arquivo.
            # Isso será útil para investigar um registro problemático depois.
            registro["_numero_linha_fonte"] = str(numero_linha)

            # Adiciona o registro bruto à lista sem limpar ou converter seus valores.
            registros.append(registro)

    # Confere se o arquivo possuía pelo menos uma linha depois do cabeçalho.
    if not registros:
        # Um CSV vazio não fornece dados para as próximas etapas do ETL.
        raise ValueError("O arquivo CSV não possui registros.")

    # Entrega os registros extraídos para a função ``transformar``.
    return registros
