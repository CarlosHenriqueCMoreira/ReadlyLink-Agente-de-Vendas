"""Gera os dados simulados de catálogo, atendimentos e vendas da Readly Link.

Os atendimentos simulam o agente de vendas ANTIGO, que tem estas falhas:

- não pergunta o orçamento do cliente;
- não liga para o tom de leitura pedido;
- nem sempre oferece o próximo volume certo de uma saga;
- em presentes, usa o gosto de quem compra e não de quem vai receber;
- quando o livro pedido está esgotado no físico, não oferece o digital.

Regra importante: um motivo de abandono só é gravado quando a causa existe.
Exemplo: "preco_acima_do_orcamento" só aparece se o preço for maior que o
orçamento do cliente.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# Pasta raiz do projeto e pasta onde ficam os CSVs.
RAIZ = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ / "data"

# A semente fixa faz o script gerar sempre os mesmos dados.
SEMENTE = 20260929

# Características de cada saga: (gênero, temas, ritmo, tom)
SAGAS = {
    "Arquivos do Céu": ("Fantasia", "mistério,conhecimento", "contemplativo", "esperançoso"),
    "As Torres de Âmbar": ("Fantasia", "aventura,reinos", "acelerado", "épico"),
    "Cidades de Sal": ("Ficção histórica", "memória,cidade", "moderado", "melancólico"),
    "Crônicas do Tempo": ("Ficção científica", "tempo,tecnologia", "acelerado", "reflexivo"),
    "Estações": ("Romance", "relacionamentos,mudança", "leve", "emocional"),
    "Ilhas Errantes": ("Aventura", "viagem,descoberta", "acelerado", "aventureiro"),
    "Jardins Secretos": ("Mistério", "segredos,família", "moderado", "intrigante"),
    "Luzes do Sul": ("Drama", "identidade,recomeço", "contemplativo", "emocional"),
    "Marés do Norte": ("Romance", "mar,família", "moderado", "nostálgico"),
    "Reinos do Bosque": ("Fantasia", "natureza,magia", "acelerado", "épico"),
    "Serra Dourada": ("Aventura", "montanha,coragem", "acelerado", "inspirador"),
    "Viajantes de Papel": ("Ficção contemporânea", "livros,amizade", "leve", "acolhedor"),
}

# O que o cliente quer quando abre o atendimento, e o peso de cada intenção.
INTENCOES = [
    "continuacao_de_saga",
    "livro_parecido",
    "presente",
    "explorar_novo_genero",
    "titulo_especifico",
]
PESOS_INTENCOES = [31, 25, 18, 14, 12]

TEXTOS_NECESSIDADE = {
    "continuacao_de_saga": "Quero continuar uma saga que comecei, mas não sei qual é o próximo volume.",
    "livro_parecido": "Quero algo parecido com os livros que costumo ler.",
    "presente": "Preciso de um livro para dar de presente e não sei qual escolher.",
    "explorar_novo_genero": "Quero experimentar um gênero novo sem pegar um livro muito difícil.",
    "titulo_especifico": "Estou procurando um título específico e quero saber se está disponível.",
}

# Etapa em que o atendimento parou, conforme o motivo do abandono.
# Texto vazio significa que a compra foi concluída.
ETAPA_POR_MOTIVO = {
    "": "PEDIDO_CONFIRMADO",
    "livro_procurado_sem_estoque": "BUSCA",
    "nao_encontrou_continuacao": "BUSCA",
    "preco_acima_do_orcamento": "RECOMENDACAO",
    "recomendacao_nao_combinou": "RECOMENDACAO",
    "apenas_pesquisando": "RECOMENDACAO",
    "abandono_no_checkout": "CHECKOUT",
}

# O sistema de origem grava 9999 para dizer "estoque ilimitado" no digital.
# O dbt transforma esse valor em nulo.
ESTOQUE_DIGITAL = 9999


def ler_usuarios():
    """Lê o CSV de usuários e devolve uma lista de dicionários."""
    caminho = PASTA_DADOS / "usuarios_readly.csv"
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def numero_do_usuario(usuario_ref):
    """Transforma "USR-000001" no número 1."""
    somente_digitos = ""
    for caractere in usuario_ref:
        if caractere.isdigit():
            somente_digitos += caractere
    return int(somente_digitos)


def separar_livros(texto_livros):
    """Separa a coluna livros_pegos em uma lista de dicionários.

    Cada livro chega assim: "13~Marés do Norte~O Último Faroleiro~volume:3~FISICO~qtd:3~data:2024-07-19"
    """
    livros = []
    for item in texto_livros.split(" || "):
        campos = item.strip().split("~")
        livros.append(
            {
                "edicao_id": int(campos[0]),
                "saga": campos[1],
                "titulo": campos[2],
                "volume": int(campos[3].replace("volume:", "")),
                "formato": campos[4].upper(),
                "quantidade": int(campos[5].replace("qtd:", "")),
                "data": campos[6].replace("data:", ""),
            }
        )
    return livros


def montar_livros(usuarios):
    """Cria o cadastro de livros: um livro por saga + volume.

    No CSV o mesmo título aparece com dois IDs (um da edição física e outro da
    digital). Aqui cada título vira um único livro, com um livro_id novo.
    """

    # Guarda o menor ID de edição e o título de cada (saga, volume).
    menor_edicao = {}
    titulos = {}
    for usuario in usuarios:
        for item in separar_livros(usuario["livros_pegos"]):
            chave = (item["saga"], item["volume"])
            titulos[chave] = item["titulo"]
            if chave not in menor_edicao or item["edicao_id"] < menor_edicao[chave]:
                menor_edicao[chave] = item["edicao_id"]

    # Ordena os livros pelo menor ID de edição e numera de 1 em diante.
    chaves_ordenadas = sorted(menor_edicao, key=lambda chave: menor_edicao[chave])

    livros = {}
    id_por_saga_volume = {}
    for posicao, chave in enumerate(chaves_ordenadas, start=1):
        saga, volume = chave
        genero, temas, ritmo, tom = SAGAS[saga]
        id_por_saga_volume[chave] = posicao
        livros[posicao] = {
            "livro_id": posicao,
            "saga": saga,
            "titulo": titulos[chave],
            "volume": volume,
            "genero": genero,
            "temas": temas,
            "ritmo": ritmo,
            "tom": tom,
            "publico_alvo": "Adulto",
        }

    return livros, id_por_saga_volume


def montar_historico(usuarios, livros, id_por_saga_volume):
    """Devolve, para cada usuário, a lista de livros que ele já leu."""
    historico = {}
    for usuario in usuarios:
        usuario_id = numero_do_usuario(usuario["usuario_ref"])
        historico[usuario_id] = []

        for item in separar_livros(usuario["livros_pegos"]):
            livro = livros[id_por_saga_volume[(item["saga"], item["volume"])]]
            historico[usuario_id].append(
                {
                    "livro_id": livro["livro_id"],
                    "saga": livro["saga"],
                    "volume": livro["volume"],
                    "genero": livro["genero"],
                    "tom": livro["tom"],
                    "formato": item["formato"],
                    "quantidade": item["quantidade"],
                    "data": item["data"],
                }
            )
    return historico


def gerar_catalogo(livros):
    """Cria dois produtos para cada livro: físico e digital."""
    catalogo = []

    for livro_id in sorted(livros):
        livro = livros[livro_id]

        for formato in ("FISICO", "DIGITAL"):
            if formato == "DIGITAL":
                preco = 8.90 + livro["volume"] * 1.75 + (livro_id % 7) * 1.30
                estoque = ESTOQUE_DIGITAL
                disponivel = "SIM"
            else:
                preco = 18.90 + livro["volume"] * 1.75 + (livro_id % 7) * 1.30
                estoque = max((livro_id * 7) % 24 - 3, 0)
                disponivel = "SIM" if estoque > 0 else "NAO"

            catalogo.append(
                {
                    "produto_id": f"{livro_id}-{formato}",
                    "livro_id": livro_id,
                    "saga": livro["saga"],
                    "titulo": livro["titulo"],
                    "volume": livro["volume"],
                    "genero": livro["genero"],
                    "temas": livro["temas"],
                    "ritmo": livro["ritmo"],
                    "tom": livro["tom"],
                    "publico_alvo": livro["publico_alvo"],
                    "formato": formato,
                    "preco": f"{preco:.2f}",
                    "estoque": estoque,
                    "disponivel": disponivel,
                    "atualizado_em": "2026-09-29 08:00:00",
                }
            )

    return catalogo


def mais_frequente(itens, campo):
    """Devolve o valor do campo que aparece mais vezes, somando a quantidade."""
    contagem = {}
    for item in itens:
        valor = item[campo]
        contagem[valor] = contagem.get(valor, 0) + item["quantidade"]

    # Maior quantidade primeiro; em caso de empate, ordem alfabética.
    ordenado = sorted(contagem.items(), key=lambda par: (-par[1], par[0]))
    return ordenado[0][0]


def perfil_do_usuario(itens):
    """Resume o histórico de um usuário."""

    # Último livro lido (pela data; no empate, o volume maior).
    ultimo_livro = max(itens, key=lambda item: (item["data"], item["volume"]))
    ultima_saga = ultimo_livro["saga"]

    # Volume mais alto que ele já leu dessa saga.
    ultimo_volume = 0
    for item in itens:
        if item["saga"] == ultima_saga and item["volume"] > ultimo_volume:
            ultimo_volume = item["volume"]

    livros_lidos = set()
    volumes_lidos = set()
    for item in itens:
        livros_lidos.add(item["livro_id"])
        volumes_lidos.add((item["saga"], item["volume"]))

    return {
        "genero": mais_frequente(itens, "genero"),
        "formato": mais_frequente(itens, "formato"),
        "tom": mais_frequente(itens, "tom"),
        "lidos": livros_lidos,
        "volumes_lidos": volumes_lidos,
        "ultima_saga": ultima_saga,
        "ultimo_volume": ultimo_volume,
    }


def recomendar_agente_antigo(genero_alvo, formato, saga_alvo, lidos, livros, ofertas, aleatorio):
    """Regra do agente antigo: gênero + saga + estoque.

    Não olha orçamento, tom nem a ordem dos volumes.
    """
    candidatos = []
    for livro in livros.values():
        livro_id = livro["livro_id"]
        oferta = ofertas[(livro_id, formato)]

        # O agente antigo pelo menos não repete livro lido nem oferece esgotado.
        if livro_id in lidos or oferta["disponivel"] != "SIM":
            continue

        pontos = 0
        if livro["genero"] == genero_alvo:
            pontos += 55
        if saga_alvo and livro["saga"] == saga_alvo:
            pontos += 25
        pontos += min(oferta["estoque"], 10)

        candidatos.append((pontos, livro_id))

    # Maior pontuação primeiro; no empate, o menor livro_id.
    candidatos.sort(key=lambda candidato: (-candidato[0], candidato[1]))

    # Escolhe ao acaso entre os primeiros colocados (até 10 pontos do melhor).
    melhor_pontuacao = candidatos[0][0]
    melhores = []
    for candidato in candidatos:
        if candidato[0] >= melhor_pontuacao - 10:
            melhores.append(candidato)

    pontos, livro_id = aleatorio.choice(melhores[:4])
    return livros[livro_id], pontos


def gerar_atendimentos_e_vendas(usuarios, livros, id_por_saga_volume, historico, catalogo, aleatorio):
    """Simula 2.400 conversas com o agente antigo e as vendas que resultaram."""

    # Acesso rápido ao produto: ofertas[(livro_id, formato)]
    ofertas = {}
    for produto in catalogo:
        ofertas[(produto["livro_id"], produto["formato"])] = produto

    # Lista de gêneros e os tons que existem em cada gênero.
    generos = sorted(set(livro["genero"] for livro in livros.values()))
    tons_por_genero = {}
    for genero, _, _, tom in SAGAS.values():
        tons_por_genero.setdefault(genero, [])
        if tom not in tons_por_genero[genero]:
            tons_por_genero[genero].append(tom)

    atendimentos = []
    vendas = []
    inicio = datetime(2026, 6, 1, 9, 0, 0)

    for indice in range(1, 2401):
        usuario = usuarios[(indice * 37) % len(usuarios)]
        usuario_id = numero_do_usuario(usuario["usuario_ref"])
        perfil = perfil_do_usuario(historico[usuario_id])

        intencao = aleatorio.choices(INTENCOES, weights=PESOS_INTENCOES, k=1)[0]
        presente = intencao == "presente"
        para_quem = "PRESENTE" if presente else "PROPRIO"

        # 1. O que o cliente pede na conversa
        if intencao == "continuacao_de_saga":
            genero_desejado = SAGAS[perfil["ultima_saga"]][0]
        elif presente:
            genero_desejado = aleatorio.choice(generos)
        elif intencao == "explorar_novo_genero":
            outros_generos = [genero for genero in generos if genero != perfil["genero"]]
            genero_desejado = aleatorio.choice(outros_generos)
        elif aleatorio.random() < 0.80:
            genero_desejado = perfil["genero"]
        else:
            genero_desejado = aleatorio.choice(generos)

        tons = sorted(tons_por_genero[genero_desejado])
        if intencao == "continuacao_de_saga":
            tom_desejado = SAGAS[perfil["ultima_saga"]][3]
        elif not presente and perfil["tom"] in tons and aleatorio.random() < 0.70:
            tom_desejado = perfil["tom"]
        else:
            tom_desejado = aleatorio.choice(tons)

        if aleatorio.random() < 0.72:
            formato_desejado = perfil["formato"]
        elif perfil["formato"] == "FISICO":
            formato_desejado = "DIGITAL"
        else:
            formato_desejado = "FISICO"

        orcamento = round(aleatorio.uniform(12, 48), 2)

        # 2. Livro que o cliente procura (próximo volume ou título específico)
        livro_procurado_id = None
        if intencao == "continuacao_de_saga":
            proximo = (perfil["ultima_saga"], perfil["ultimo_volume"] + 1)
            livro_procurado_id = id_por_saga_volume.get(proximo)
        elif intencao == "titulo_especifico":
            opcoes = []
            for livro in livros.values():
                if livro["genero"] == genero_desejado and livro["livro_id"] not in perfil["lidos"]:
                    opcoes.append(livro["livro_id"])
            if not opcoes:
                for livro in livros.values():
                    if livro["livro_id"] not in perfil["lidos"]:
                        opcoes.append(livro["livro_id"])
            livro_procurado_id = aleatorio.choice(sorted(opcoes))

        procurado_disponivel = False
        if livro_procurado_id is not None:
            procurado_disponivel = ofertas[(livro_procurado_id, formato_desejado)]["disponivel"] == "SIM"

        # 3. O que o agente antigo recomendou
        if intencao == "titulo_especifico" and procurado_disponivel:
            livro = livros[livro_procurado_id]
            pontuacao = 90
        elif intencao == "continuacao_de_saga" and procurado_disponivel and aleatorio.random() < 0.50:
            livro = livros[livro_procurado_id]
            pontuacao = 90
        else:
            # Falha do agente antigo: em presentes usa o gosto de quem compra.
            genero_alvo = perfil["genero"] if presente else genero_desejado
            saga_alvo = perfil["ultima_saga"] if intencao == "continuacao_de_saga" else None
            livro, pontuacao = recomendar_agente_antigo(
                genero_alvo, formato_desejado, saga_alvo, perfil["lidos"], livros, ofertas, aleatorio
            )

        oferta = ofertas[(livro["livro_id"], formato_desejado)]
        preco = float(oferta["preco"])
        genero_ok = livro["genero"] == genero_desejado
        tom_ok = livro["tom"] == tom_desejado
        volume_anterior_lido = (livro["saga"], livro["volume"] - 1) in perfil["volumes_lidos"]
        volume_ok = livro["volume"] == 1 or (not presente and volume_anterior_lido)

        # 4. Motivo do abandono: só existe quando a causa existe.
        # Cada condição tem uma chance; se o cliente "aceitar" o problema,
        # passa para a condição seguinte.
        motivo = ""
        if intencao == "titulo_especifico" and not procurado_disponivel and aleatorio.random() < 0.80:
            motivo = "livro_procurado_sem_estoque"
        elif intencao == "continuacao_de_saga" and livro["livro_id"] != livro_procurado_id and aleatorio.random() < 0.75:
            motivo = "nao_encontrou_continuacao"
        elif preco > orcamento and aleatorio.random() < 0.80:
            motivo = "preco_acima_do_orcamento"
        elif not genero_ok and aleatorio.random() < 0.70:
            motivo = "recomendacao_nao_combinou"
        elif not tom_ok and aleatorio.random() < 0.15:
            motivo = "recomendacao_nao_combinou"
        elif not volume_ok and aleatorio.random() < 0.30:
            motivo = "recomendacao_nao_combinou"

        # Sem problema na recomendação: a maioria compra.
        if motivo == "":
            sorteio = aleatorio.random()
            if sorteio >= 0.91:
                motivo = "apenas_pesquisando"
            elif sorteio >= 0.80:
                motivo = "abandono_no_checkout"

        compra_concluida = motivo == ""
        etapa_final = ETAPA_POR_MOTIVO[motivo]

        if compra_concluida:
            avaliacao = aleatorio.choices([4, 5], weights=[35, 65], k=1)[0]
        else:
            avaliacao = aleatorio.choices([1, 2, 3, 4], weights=[8, 22, 50, 20], k=1)[0]

        atendimento_id = f"ATD-{indice:06d}"
        momento = inicio + timedelta(minutes=indice * 71 + aleatorio.randint(0, 50))

        if etapa_final in ("CHECKOUT", "PEDIDO_CONFIRMADO"):
            recomendacao_aceita = "SIM"
        else:
            recomendacao_aceita = "NAO"

        atendimentos.append(
            {
                "atendimento_id": atendimento_id,
                "usuario_id": usuario_id,
                "iniciado_em": momento.strftime("%Y-%m-%d %H:%M:%S"),
                "necessidade_declarada": TEXTOS_NECESSIDADE[intencao],
                "intencao": intencao,
                "para_quem": para_quem,
                "genero_desejado": genero_desejado,
                "tom_desejado": tom_desejado,
                "formato_desejado": formato_desejado,
                "orcamento": f"{orcamento:.2f}",
                "livro_procurado_id": livro_procurado_id if livro_procurado_id else "",
                "livro_recomendado_id": livro["livro_id"],
                "formato_recomendado": oferta["formato"],
                "preco_informado": oferta["preco"],
                "estoque_informado": oferta["estoque"],
                "pontuacao_recomendacao": pontuacao,
                "recomendacao_aceita": recomendacao_aceita,
                "etapa_final": etapa_final,
                "resultado": "VENDA_CONCLUIDA" if compra_concluida else "SEM_COMPRA",
                "motivo_abandono": motivo,
                "avaliacao": avaliacao,
                "custo_ia_eur": f"{aleatorio.uniform(0.012, 0.058):.4f}",
            }
        )

        # 5. Se comprou, cria o pedido
        if compra_concluida:
            quantidade = aleatorio.choices([1, 2], weights=[92, 8], k=1)[0]
            criado_em = momento + timedelta(minutes=aleatorio.randint(3, 18))
            vendas.append(
                {
                    "pedido_id": f"PED-{len(vendas) + 1:06d}",
                    "atendimento_id": atendimento_id,
                    "usuario_id": usuario_id,
                    "produto_id": oferta["produto_id"],
                    "livro_id": livro["livro_id"],
                    "formato": oferta["formato"],
                    "quantidade": quantidade,
                    "preco_unitario": f"{preco:.2f}",
                    "valor_total": f"{preco * quantidade:.2f}",
                    "pagamento_status": "TESTE_APROVADO",
                    "aprovacao_humana": "APROVADA",
                    "documento_status": "SIMULADO_APROVADO",
                    "criado_em": criado_em.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return atendimentos, vendas


def gerar_dados():
    """Gera catálogo, atendimentos e vendas sem gravar arquivos (usado nos testes)."""
    aleatorio = random.Random(SEMENTE)
    usuarios = ler_usuarios()
    livros, id_por_saga_volume = montar_livros(usuarios)
    historico = montar_historico(usuarios, livros, id_por_saga_volume)
    catalogo = gerar_catalogo(livros)
    atendimentos, vendas = gerar_atendimentos_e_vendas(
        usuarios, livros, id_por_saga_volume, historico, catalogo, aleatorio
    )
    return catalogo, atendimentos, vendas


def escrever_csv(nome_arquivo, registros):
    caminho = PASTA_DADOS / nome_arquivo
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]))
        escritor.writeheader()
        escritor.writerows(registros)


def main():
    catalogo, atendimentos, vendas = gerar_dados()
    escrever_csv("catalogo_livros.csv", catalogo)
    escrever_csv("atendimentos.csv", atendimentos)
    escrever_csv("vendas.csv", vendas)
    print(
        f"Dados de negócio gerados: {len(catalogo)} ofertas, "
        f"{len(atendimentos)} atendimentos e {len(vendas)} vendas."
    )


if __name__ == "__main__":
    main()
