from etl.transform import transformar


def test_transformar_remove_espacos_e_cria_hash():
    entrada = [
        {
            "usuario_ref": " USR-000001 ",
            "nome_completo": " Ana Silva ",
            "idade": " 30 anos ",
            "tipo_documento": " cpf ",
            "documento": " TESTE-CPF-000001 ",
            "livros_pegos": "1~Saga~Livro~volume:1~FISICO~qtd:1~data:2026-01-01",
            "_numero_linha_fonte": "2",
        }
    ]

    resultado = transformar(entrada)[0]

    assert resultado["usuario_ref"] == "USR-000001"
    assert resultado["idade"] == "30 anos"
    assert resultado["_numero_linha_fonte"] == 2
    assert len(resultado["registro_hash"]) == 64


def test_transformar_rejeita_campo_obrigatorio_vazio():
    entrada = [
        {
            "usuario_ref": "",
            "nome_completo": "Ana Silva",
            "idade": "30",
            "tipo_documento": "CPF",
            "documento": "TESTE-CPF-000001",
            "livros_pegos": "1~Saga~Livro~volume:1~FISICO~qtd:1~data:2026-01-01",
            "_numero_linha_fonte": "2",
        }
    ]

    try:
        transformar(entrada)
    except ValueError as erro:
        assert "usuario_ref" in str(erro)
    else:
        raise AssertionError("Era esperado ValueError para usuario_ref vazio.")
