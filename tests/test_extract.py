import pytest

from etl.extract import extrair


CABECALHO = (
    "usuario_ref,nome_completo,idade,tipo_documento,documento,livros_pegos\n"
)


def test_extrair_csv_valido_adiciona_numero_da_linha(tmp_path):
    arquivo = tmp_path / "usuarios.csv"
    arquivo.write_text(
        CABECALHO
        + "USR-1,Ana Silva,30,CPF,TESTE-CPF-1,"
        + "1~Saga~Livro~volume:1~FISICO~qtd:1~data:2026-01-01\n",
        encoding="utf-8",
    )

    registros = extrair(arquivo)

    assert len(registros) == 1
    assert registros[0]["usuario_ref"] == "USR-1"
    assert registros[0]["_numero_linha_fonte"] == "2"


def test_extrair_rejeita_coluna_obrigatoria_ausente(tmp_path):
    arquivo = tmp_path / "usuarios.csv"
    arquivo.write_text("usuario_ref,nome_completo\n1,Ana Silva\n", encoding="utf-8")

    with pytest.raises(ValueError, match="colunas obrigatórias"):
        extrair(arquivo)
