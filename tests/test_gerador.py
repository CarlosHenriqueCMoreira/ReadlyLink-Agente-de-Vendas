"""Garante que os dados simulados são coerentes com os motivos registrados."""

from collections import Counter

import pytest

from gerar_dados_negocio import gerar_dados


@pytest.fixture(scope="module")
def dados():
    catalogo, atendimentos, vendas = gerar_dados()
    return catalogo, atendimentos, vendas


def test_catalogo_tem_uma_obra_por_saga_e_volume(dados):
    catalogo, _, _ = dados
    obras = {(item["saga"], item["volume"]) for item in catalogo}
    ids = {item["livro_id"] for item in catalogo}
    assert len(obras) == len(ids) == 48
    assert Counter(item["formato"] for item in catalogo) == {"FISICO": 48, "DIGITAL": 48}


def test_digital_sempre_disponivel(dados):
    catalogo, _, _ = dados
    digitais = [item for item in catalogo if item["formato"] == "DIGITAL"]
    assert all(item["disponivel"] == "SIM" for item in digitais)


def test_motivo_preco_so_existe_com_preco_acima_do_orcamento(dados):
    _, atendimentos, _ = dados
    casos = [a for a in atendimentos if a["motivo_abandono"] == "preco_acima_do_orcamento"]
    assert casos
    assert all(float(a["preco_informado"]) > float(a["orcamento"]) for a in casos)


def test_sem_estoque_so_existe_com_livro_procurado(dados):
    catalogo, atendimentos, _ = dados
    disponivel = {(i["livro_id"], i["formato"]): i["disponivel"] == "SIM" for i in catalogo}
    casos = [a for a in atendimentos if a["motivo_abandono"] == "livro_procurado_sem_estoque"]
    assert casos
    for a in casos:
        assert a["livro_procurado_id"] != ""
        assert not disponivel[(a["livro_procurado_id"], a["formato_desejado"])]


def test_continuacao_so_existe_quando_o_volume_oferecido_e_outro(dados):
    _, atendimentos, _ = dados
    casos = [a for a in atendimentos if a["motivo_abandono"] == "nao_encontrou_continuacao"]
    assert casos
    assert all(a["intencao"] == "continuacao_de_saga" for a in casos)
    assert all(a["livro_recomendado_id"] != a["livro_procurado_id"] for a in casos)


def test_toda_venda_vem_de_um_atendimento_concluido(dados):
    _, atendimentos, vendas = dados
    concluidos = {a["atendimento_id"] for a in atendimentos if a["resultado"] == "VENDA_CONCLUIDA"}
    assert {v["atendimento_id"] for v in vendas} == concluidos
    assert all(a["motivo_abandono"] == "" for a in atendimentos if a["resultado"] == "VENDA_CONCLUIDA")
