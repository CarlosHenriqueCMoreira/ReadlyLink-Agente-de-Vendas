from etl.extract import extrair
from etl.transform import transformar
from etl.load import carregar
from etl.load_business import carregar_dados_negocio


def main():
    caminho_arquivo = "data/usuarios_readly.csv"

    dados_extraidos = extrair(caminho_arquivo)
    dados_tratados = transformar(dados_extraidos)
    carregar(dados_tratados)
    carregar_dados_negocio("data")


if __name__ == "__main__":
    main()