"""Escreve as respostas às 23 perguntas do cliente.

Lê o JSON criado por exportar_metricas.py, monta o texto de cada resposta com
os números do banco e grava:

- docs/respostas_perguntas.md (para ler no GitHub);
- as respostas dentro do mesmo JSON (para a página visual).

Nenhum número é escrito à mão: todos vêm do JSON.
"""

import json
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
ARQUIVO_JSON = RAIZ_PROJETO / "readly_dbt" / "target" / "business_metrics.json"
ARQUIVO_RESPOSTAS = RAIZ_PROJETO / "docs" / "respostas_perguntas.md"


ROTULOS_MOTIVO = {
    "preco_acima_do_orcamento": "Preço acima do orçamento",
    "recomendacao_nao_combinou": "Recomendação não combinou",
    "abandono_no_checkout": "Abandono no checkout",
    "apenas_pesquisando": "Cliente estava apenas pesquisando",
    "nao_encontrou_continuacao": "Não encontrou a continuação da saga",
    "livro_procurado_sem_estoque": "Livro procurado sem estoque",
}

# Frase de evidência de cada motivo, usada na resposta 7.
EVIDENCIA_MOTIVO = {
    "preco_acima_do_orcamento": "em todos o preço era maior que o orçamento, em média {diferenca} acima",
    "recomendacao_nao_combinou": "todos receberam um livro de outro gênero, outro tom ou que pulava volume; {presentes} eram presentes",
    "nao_encontrou_continuacao": "em todos o agente não ofereceu o próximo volume da saga",
    "livro_procurado_sem_estoque": "em todos o título pedido estava indisponível no formato escolhido",
    "abandono_no_checkout": "aceitaram o livro e saíram no pagamento",
    "apenas_pesquisando": "viram a recomendação sem intenção de comprar agora",
}

ROTULOS_ACAO = {
    "OFERECER_OPCAO_NO_ORCAMENTO": "Oferecer opção adequada dentro do orçamento",
    "REFAZER_RECOMENDACAO": "Refazer a recomendação com as regras novas",
    "RETOMAR_CHECKOUT": "Retomar o checkout com o mesmo livro",
    "RETOMAR_CHECKOUT_COM_OPCAO_ADEQUADA": "Retomar o checkout com uma opção adequada",
    "SALVAR_LISTA_E_LEMBRAR": "Guardar a sugestão e enviar lembrete",
    "OFERECER_PROXIMO_VOLUME": "Oferecer o próximo volume da saga",
    "OFERECER_SAGA_SEMELHANTE": "Saga concluída: oferecer o início de uma saga semelhante",
    "OFERECER_OUTRO_FORMATO_E_AVISAR_REPOSICAO": "Oferecer o mesmo livro no outro formato e avisar da reposição",
    "OFERECER_SIMILAR_E_AVISAR_REPOSICAO": "Oferecer um livro semelhante e avisar da reposição",
}

# (pergunta, campo do atendimento que ela preenche, por que perguntar)
PERGUNTAS_VENDEDOR = [
    ("É para você ou para presente?", "para_quem",
     "Define quem vai ler. Em presentes o histórico de quem compra não é usado."),
    ("Que gênero você quer ler agora?", "genero_desejado",
     "O pedido de hoje pesa mais do que o gênero mais lido no passado."),
    ("Que tom de leitura procura (épico, leve, emocional, intrigante...)?", "tom_desejado",
     "Evita um livro do gênero certo com a atmosfera errada."),
    ("Prefere físico ou digital?", "formato_desejado",
     "Define a oferta e a disponibilidade. O digital é sempre disponível e mais barato."),
    ("Qual é o orçamento máximo?", "orcamento",
     "Nenhuma recomendação pode passar deste valor."),
]

REGRAS_ADEQUADO = [
    "Está disponível no formato oferecido (o digital é sempre disponível)",
    "Cabe no orçamento declarado pelo cliente",
    "O cliente ainda não leu (em presentes, o histórico de quem compra não conta)",
    "Respeita a ordem da saga: volume 1 ou o volume anterior já foi lido (presentes: só volume 1)",
    "É do gênero pedido, ou é exatamente o livro que o cliente pediu pelo nome",
]

GRUPOS = {
    "diagnostico": "Diagnóstico",
    "solucoes": "Soluções produzidas pelo sistema",
    "vendedor": "Método do vendedor",
    "exemplo": "Exemplo explicável",
}


# ------------------------------------------------------------------ formatação

def num(valor):
    """1234 -> "1.234" """
    return f"{int(round(valor)):,}".replace(",", ".")


def pct(valor):
    """61.23 -> "61,2%" """
    return f"{valor:.1f}".replace(".", ",") + "%"


def eur(valor):
    """1234.5 -> "1.234,50 €" """
    texto = f"{valor:,.2f}"                       # 1,234.50
    texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return texto + " €"


def vai_ou_vao(quantidade):
    """1 -> "1 vai", 5 -> "5 vão" """
    if int(quantidade) == 1:
        return f"{num(quantidade)} vai"
    return f"{num(quantidade)} vão"


def texto_estoque(estoque, ilimitado):
    if ilimitado:
        return "Digital · sempre disponível"
    return f"{num(estoque)} unidades em estoque"


def antes_depois_texto(linha):
    """Linha do mart_antes_depois -> "72,6% → 93,9%" """
    return f"{pct(linha['antes_percentual'])} → {pct(linha['depois_percentual'])}"


def exemplo_solucao(exemplo):
    """Frase de exemplo usada nas respostas 9, 10 e 14."""
    if exemplo["motivo_abandono"] == "livro_procurado_sem_estoque":
        return (
            f" Exemplo ({exemplo['atendimento_id']}): o cliente procurava «{exemplo['titulo_procurado']}» em físico, "
            f"que está esgotado; agora recebe «{exemplo['titulo_solucao']}» em "
            f"{exemplo['formato_solucao'].lower()} por {eur(exemplo['preco_solucao'])} (orçamento {eur(exemplo['orcamento'])})."
        )
    return (
        f" Exemplo ({exemplo['atendimento_id']}): orçamento de {eur(exemplo['orcamento'])}; antes foi oferecido "
        f"«{exemplo['titulo_recomendado']}» por {eur(exemplo['preco_informado'])}; agora o sistema oferece "
        f"«{exemplo['titulo_solucao']}» ({exemplo['formato_solucao'].lower()}, {eur(exemplo['preco_solucao'])})."
    )


def resposta(numero, grupo, pergunta, destaque, destaque_rotulo, texto):
    return {
        "id": numero,
        "grupo": grupo,
        "pergunta": pergunta,
        "destaque": destaque,
        "destaque_rotulo": destaque_rotulo,
        "resposta": texto,
    }


# ------------------------------------------------------------------ respostas

def montar_respostas(dados):
    # --- Separar os dados em variáveis com nomes simples ---
    totais = dados["totais"]
    qualidade = dados["qualidade"]
    contagens = dados["contagens_solucoes"]
    exemplo = dados["exemplo"]

    motivos_ordenados = dados["motivos_abandono"]  # já vem do maior para o menor
    motivos = {linha["motivo_abandono"]: linha for linha in motivos_ordenados}
    funil = {linha["ordem"]: linha for linha in dados["funil"]}
    antes_depois = {linha["ordem"]: linha for linha in dados["antes_depois"]}
    solucoes = {linha["motivo_abandono"]: linha for linha in dados["resultados_solucoes"]}
    exemplos = {linha["motivo_abandono"]: linha for linha in dados["exemplos_solucoes"]}

    atendimentos = qualidade["atendimentos"]
    sem_compra = totais["sem_compra"]
    automaticas = contagens["automaticas"]
    revisao_humana = contagens["revisao_humana"]

    perdidos_busca = funil[2]["perdidos_nesta_etapa"]
    perdidos_recomendacao = funil[3]["perdidos_nesta_etapa"]
    perdidos_checkout = funil[4]["perdidos_nesta_etapa"]

    orcamento_ok = antes_depois[1]
    genero_ok = antes_depois[2]
    tom_ok = antes_depois[3]
    volume_ok = antes_depois[4]
    proximo_volume = antes_depois[5]
    titulo_procurado = antes_depois[6]
    presentes = antes_depois[7]
    adequado = antes_depois[8]

    preco = solucoes["preco_acima_do_orcamento"]
    nao_combinou = solucoes["recomendacao_nao_combinou"]
    checkout = solucoes["abandono_no_checkout"]
    pesquisando = solucoes["apenas_pesquisando"]
    continuacao = solucoes["nao_encontrou_continuacao"]
    sem_estoque = solucoes["livro_procurado_sem_estoque"]
    motivo_estoque = motivos["livro_procurado_sem_estoque"]

    # Resposta 1: as três maiores causas
    tres_maiores = motivos_ordenados[:3]
    partes = []
    soma_percentual = 0
    for linha in tres_maiores:
        partes.append(f"{ROTULOS_MOTIVO[linha['motivo_abandono']].lower()} ({num(linha['atendimentos'])})")
        soma_percentual += linha["percentual_abandonos"]

    # Resposta 7: uma frase por motivo
    frases_motivos = []
    for linha in motivos_ordenados:
        evidencia = EVIDENCIA_MOTIVO[linha["motivo_abandono"]].format(
            diferenca=eur(linha["diferenca_media_preco_orcamento"]),
            presentes=num(linha["casos_presente"]),
        )
        frases_motivos.append(
            f"{ROTULOS_MOTIVO[linha['motivo_abandono']]}: {num(linha['atendimentos'])} "
            f"({pct(linha['percentual_abandonos'])}) — {evidencia}."
        )

    # Resposta 16: motivos da revisão humana
    frases_revisao = []
    for linha in dados["revisao"]:
        frases_revisao.append(f"{linha['motivo_revisao']}: {num(linha['casos'])}")

    # Resposta 17: perguntas numeradas
    frases_perguntas = []
    for posicao, (pergunta, _, motivo) in enumerate(PERGUNTAS_VENDEDOR, start=1):
        frases_perguntas.append(f"{posicao}. {pergunta} ({motivo})")

    # Resposta 18: regras com a primeira letra minúscula
    regras_minusculas = []
    for regra in REGRAS_ADEQUADO:
        regras_minusculas.append(regra[0].lower() + regra[1:])

    estoque_exemplo = texto_estoque(exemplo["estoque"], exemplo["estoque_ilimitado"])
    para_quem = "a própria cliente" if exemplo["para_quem"] == "PROPRIO" else "presente"

    return [
        # ---------------------------------------------------------- diagnóstico
        resposta(
            1, "diagnostico", "O que está impedindo o cliente de comprar?",
            pct(100 * sem_compra / atendimentos), "dos atendimentos terminam sem compra",
            f"{num(sem_compra)} de {num(atendimentos)} atendimentos terminaram sem compra. "
            f"As três maiores causas são {', '.join(partes)}, que juntas somam {pct(soma_percentual)} "
            "dos abandonos. As três vêm do atendimento antigo: recomendar sem perguntar o orçamento, "
            "ignorar o gosto de quem vai ler e errar o volume da saga.",
        ),
        resposta(
            2, "diagnostico", "A Readly Link entende o que a pessoa quer ler?",
            antes_depois_texto(presentes), "presentes no gênero de quem recebe (antes → depois)",
            "Só em parte. O agente antigo usava o gênero mais lido do histórico e ignorava o tom pedido e "
            f"quem ia receber o presente: {pct(tom_ok['antes_percentual'])} das recomendações respeitavam o tom "
            f"pedido e só {pct(presentes['antes_percentual'])} dos presentes eram do gênero de quem recebe. "
            "Com as cinco perguntas novas (para quem, gênero, tom, formato e orçamento), o tom passa para "
            f"{pct(tom_ok['depois_percentual'])} e os presentes para {pct(presentes['depois_percentual'])}. "
            f"Os {num(totais['perfis'])} clientes têm perfil de leitura calculado a partir do histórico.",
        ),
        resposta(
            3, "diagnostico", "A recomendação de livros está funcionando?",
            antes_depois_texto(adequado), "recomendações que cumprem todas as regras",
            f"Não. Só {pct(adequado['antes_percentual'])} das recomendações antigas cumpriam todas as regras de "
            f"livro adequado: {num(qualidade['recomendacoes_acima_orcamento'])} estavam acima do orçamento e "
            f"{num(volume_ok['base'] - volume_ok['antes'])} pulavam volume de saga. A aceitação foi de "
            f"{pct(qualidade['taxa_aceitacao_percentual'])}. Com o motor de regras, {pct(adequado['depois_percentual'])} "
            "dos atendimentos recebem um livro adequado. Os restantes não têm opção que cumpra as regras "
            "e vão para um vendedor.",
        ),
        resposta(
            4, "diagnostico", "O estoque ainda faz a empresa perder vendas?",
            num(motivo_estoque["atendimentos"]), "vendas perdidas por falta de estoque",
            f"Pouco, mas perde. {num(motivo_estoque['atendimentos'])} abandonos "
            f"({pct(motivo_estoque['percentual_abandonos'])}) aconteceram porque o "
            f"título pedido estava sem estoque no formato escolhido. {num(totais['fisicos_sem_estoque'])} dos "
            f"{num(totais['fisicos'])} livros físicos estão esgotados. O agente antigo não inventava estoque "
            f"({num(qualidade['divergencias_preco'])} divergências de preço e {num(qualidade['recomendacoes_sem_estoque'])} "
            "produtos indisponíveis recomendados). O que faltava era oferecer o mesmo livro no formato digital.",
        ),
        resposta(
            5, "diagnostico", "A venda chega até o fim?",
            pct(qualidade["conversao_percentual"]), "de conversão",
            f"Em {pct(qualidade['conversao_percentual'])} dos casos. De {num(atendimentos)} atendimentos, "
            f"{num(funil[2]['quantidade'])} passaram da busca, {num(funil[3]['quantidade'])} aceitaram a "
            f"recomendação e foram ao checkout e {num(funil[4]['quantidade'])} concluíram a compra. A maior "
            f"perda está na recomendação ({num(perdidos_recomendacao)} clientes). No checkout saem {num(perdidos_checkout)}.",
        ),
        resposta(
            6, "diagnostico", "Como o atendimento funciona atualmente e onde ele falha?",
            num(perdidos_recomendacao), "clientes perdidos na etapa de recomendação",
            "O cliente diz o que procura e o agente recomenda um livro usando só o gênero mais lido, a saga e "
            "o estoque. Não pergunta o orçamento, o tom nem para quem é. Falha em três pontos: na busca "
            f"({num(perdidos_busca)} não encontraram a continuação ou o título), na recomendação "
            f"({num(perdidos_recomendacao)} recusaram pelo preço, por não combinar ou só estavam pesquisando) e no "
            f"checkout ({num(perdidos_checkout)}).",
        ),
        resposta(
            7, "diagnostico", "Por que os clientes abandonam a compra?",
            pct(motivos_ordenados[0]["percentual_abandonos"]),
            ROTULOS_MOTIVO[motivos_ordenados[0]["motivo_abandono"]].lower(),
            " ".join(frases_motivos),
        ),
        resposta(
            8, "diagnostico", "O que estava ruim e o que a solução mudou?",
            antes_depois_texto(orcamento_ok), "recomendações dentro do orçamento",
            f"Nos mesmos {num(atendimentos)} atendimentos: dentro do orçamento {antes_depois_texto(orcamento_ok)}; "
            f"gênero pedido {antes_depois_texto(genero_ok)}; tom pedido {antes_depois_texto(tom_ok)}; "
            f"sem pular volume {antes_depois_texto(volume_ok)}; próximo volume certo {antes_depois_texto(proximo_volume)}; "
            f"título procurado oferecido {antes_depois_texto(titulo_procurado)}; presentes no gênero de quem recebe "
            f"{antes_depois_texto(presentes)}; livro adequado {antes_depois_texto(adequado)}. Isto mede o cumprimento "
            "das regras. O efeito nas vendas só pode ser medido depois que o novo atendimento estiver em produção.",
        ),
        # ------------------------------------------------------------ soluções
        resposta(
            9, "solucoes", "Que solução o sistema produziu para os clientes com orçamento insuficiente?",
            f"{num(preco['casos_com_solucao'])}/{num(preco['casos_encontrados'])}",
            "receberam uma opção dentro do orçamento",
            f"Para os {num(preco['casos_encontrados'])} clientes que recusaram pelo preço, o sistema procura "
            "um livro adequado que caiba no orçamento. Primeiro tenta o mesmo livro no outro formato (o "
            "digital custa cerca de 10 € menos) e depois outro título do gênero pedido. "
            f"{num(preco['casos_com_solucao'])} ({pct(preco['cobertura_percentual'])}) receberam uma opção, "
            f"com preço médio de {eur(preco['preco_medio_solucao'])} para um orçamento médio de "
            f"{eur(preco['orcamento_medio'])}. {vai_ou_vao(preco['casos_para_revisao_humana'])} para revisão "
            "humana porque nenhum livro adequado cabe no orçamento."
            + exemplo_solucao(exemplos["preco_acima_do_orcamento"]),
        ),
        resposta(
            10, "solucoes", "Que solução foi produzida para recomendações que não combinaram?",
            f"{num(nao_combinou['casos_com_solucao'])}/{num(nao_combinou['casos_encontrados'])}",
            "receberam uma nova recomendação",
            "O sistema refaz a recomendação com as regras novas: gênero e tom pedidos, sem pular volume, "
            "dentro do orçamento, ainda não lido e, de preferência, de outra saga. Em presentes usa o gosto "
            f"de quem vai receber. {num(nao_combinou['casos_com_solucao'])} de {num(nao_combinou['casos_encontrados'])} "
            f"receberam um livro novo e {vai_ou_vao(nao_combinou['casos_para_revisao_humana'])} para revisão."
            + exemplo_solucao(exemplos["recomendacao_nao_combinou"]),
        ),
        resposta(
            11, "solucoes", "Como o sistema trata clientes que abandonaram o checkout?",
            f"{num(checkout['casos_com_solucao'])}/{num(checkout['casos_encontrados'])}",
            "com checkout retomado",
            "Retoma o checkout. Se o livro escolhido ainda cumpre as regras, o cliente recebe o mesmo "
            f"carrinho ({num(contagens['checkout_mesmo_livro'])} casos). Se o livro estava acima "
            "do orçamento ou pulava volume, recebe uma opção adequada "
            f"({num(contagens['checkout_outro_livro'])} casos). "
            f"{vai_ou_vao(checkout['casos_para_revisao_humana'])} para revisão.",
        ),
        resposta(
            12, "solucoes", "Como o sistema trata clientes que estavam apenas pesquisando?",
            f"{num(pesquisando['casos_com_solucao'])}/{num(pesquisando['casos_encontrados'])}",
            "com lista guardada e lembrete",
            "Não força a venda. Guarda uma lista com a melhor sugestão adequada e envia um lembrete depois. "
            f"Se o livro visto já cumpria as regras, fica o mesmo ({num(contagens['pesquisando_mesmo_livro'])}). "
            f"Se não, é trocado por um adequado ({num(contagens['pesquisando_outro_livro'])}). "
            f"{vai_ou_vao(pesquisando['casos_para_revisao_humana'])} para revisão.",
        ),
        resposta(
            13, "solucoes", "Como o sistema ajuda quem não encontrou a continuação de uma saga?",
            f"{num(continuacao['casos_com_solucao'])}/{num(continuacao['casos_encontrados'])}",
            "receberam o próximo volume ou uma saga semelhante",
            "Identifica a última saga lida e o último volume. "
            f"{num(contagens['continuacao_proximo_volume'])} clientes recebem o próximo volume, no formato que "
            f"cabe no orçamento. {num(contagens['continuacao_saga_semelhante'])} já tinham terminado a saga "
            "(não existe continuação) e recebem o volume 1 de uma saga do mesmo gênero ou tom. "
            f"{vai_ou_vao(continuacao['casos_para_revisao_humana'])} para revisão: "
            f"{num(contagens['continuacao_revisao_orcamento'])} porque o próximo volume não cabe no orçamento e "
            f"{num(contagens['continuacao_revisao_sem_saga'])} porque não há saga semelhante disponível.",
        ),
        resposta(
            14, "solucoes", "O que o sistema oferece quando o livro procurado está sem estoque?",
            f"{num(sem_estoque['casos_com_solucao'])}/{num(sem_estoque['casos_encontrados'])}",
            "receberam uma alternativa",
            f"Primeiro, o mesmo livro no outro formato ({num(contagens['estoque_outro_formato'])} casos). "
            "Se não couber no orçamento, um livro semelhante do mesmo gênero "
            f"({num(contagens['estoque_similar'])}). "
            "Nos dois casos o cliente é avisado quando o físico voltar ao estoque. "
            f"{vai_ou_vao(sem_estoque['casos_para_revisao_humana'])} para revisão."
            + exemplo_solucao(exemplos["livro_procurado_sem_estoque"]),
        ),
        resposta(
            15, "solucoes", "Quantos casos receberam uma solução automática?",
            num(automaticas), f"de {num(sem_compra)} abandonos ({pct(100 * automaticas / sem_compra)})",
            f"{num(automaticas)} de {num(sem_compra)} atendimentos sem compra ({pct(100 * automaticas / sem_compra)}). "
            f"{num(contagens['acao_pronta'])} têm ação pronta (o livro original já cumpria as regras) e "
            f"{num(contagens['alternativa'])} receberam uma alternativa. Todas passam nos testes automáticos: "
            "livro disponível, dentro do orçamento, ainda não lido e sem pular volume.",
        ),
        resposta(
            16, "solucoes", "Quantos casos precisam de revisão humana?",
            num(revisao_humana), f"casos ({pct(100 * revisao_humana / sem_compra)} dos abandonos)",
            f"{num(revisao_humana)} ({pct(100 * revisao_humana / sem_compra)}). "
            + "; ".join(frases_revisao)
            + ". Nestes casos nenhum livro cumpre todas as regras, e o sistema não inventa uma alternativa.",
        ),
        # -------------------------------------------------- método do vendedor
        resposta(
            17, "vendedor", "Que perguntas o vendedor deve fazer antes de recomendar?",
            "5", "perguntas, cada uma ligada a uma regra",
            " ".join(frases_perguntas),
        ),
        resposta(
            18, "vendedor", "O que torna um livro adequado para o cliente?",
            "5", "regras verificadas em todos os atendimentos",
            "Um livro é adequado quando cumpre as cinco regras: " + "; ".join(regras_minusculas) + ".",
        ),
        resposta(
            19, "vendedor", "O que torna um livro inadequado?",
            num(atendimentos - adequado["antes"]), "recomendações antigas inadequadas",
            "Violar qualquer uma das regras: estar acima do orçamento, ser de outro gênero, pular um volume "
            "da saga, repetir um livro já lido ou estar indisponível. No atendimento antigo: "
            f"{num(qualidade['recomendacoes_acima_orcamento'])} acima do orçamento, "
            f"{num(genero_ok['base'] - genero_ok['antes'])} de outro gênero, "
            f"{num(volume_ok['base'] - volume_ok['antes'])} pulavam volume e "
            f"{num(tom_ok['base'] - tom_ok['antes'])} tinham outro tom. Tom diferente reduz a pontuação, mas "
            "sozinho não elimina o livro.",
        ),
        resposta(
            20, "vendedor", "Como o vendedor consegue explicar e justificar uma recomendação?",
            "100", "pontos divididos por regra",
            "Cada recomendação traz uma pontuação de 0 a 100 dividida por critério (livro pedido 30, "
            "gênero 30, tom 15, formato 15, folga no orçamento até 10) e uma frase gerada com os dados do "
            f"cliente. Exemplo: «{exemplo['justificativa']}».",
        ),
        # ------------------------------------------------------------- exemplo
        resposta(
            21, "exemplo", "Qual livro foi recomendado no exemplo?",
            exemplo["titulo"], f"{exemplo['saga']} · volume {exemplo['volume']}",
            f"«{exemplo['titulo']}», volume {exemplo['volume']} da saga {exemplo['saga']}, em formato "
            f"{exemplo['formato'].lower()}, para {exemplo['nome_completo']} ({exemplo['atendimento_id']}). "
            f"Antes, o agente antigo tinha oferecido «{exemplo['titulo_antes']}» (volume {exemplo['volume_antes']}), "
            "e a cliente saiu sem comprar porque não encontrou a continuação.",
        ),
        resposta(
            22, "exemplo", "Quais dados do cliente levaram a essa recomendação?",
            f"vol. {exemplo['ultimo_volume_lido']} → {exemplo['volume']}",
            f"último volume lido de {exemplo['ultima_saga']}",
            f"Pedido: «{exemplo['necessidade_declarada']}» Para: {para_quem}. "
            f"Gênero {exemplo['genero_desejado']}, tom {exemplo['tom_desejado']}, "
            f"formato {exemplo['formato_desejado'].lower()}, orçamento {eur(exemplo['orcamento'])}. "
            f"Histórico: {num(exemplo['livros_lidos'])} livros lidos, última saga {exemplo['ultima_saga']} "
            f"até o volume {exemplo['ultimo_volume_lido']}, gênero preferido {exemplo['genero_preferido']} "
            f"e formato preferido {exemplo['formato_preferido'].lower()}.",
        ),
        resposta(
            23, "exemplo", "Qual é o preço, estoque e pontuação do livro recomendado?",
            eur(exemplo["preco"]), f"{estoque_exemplo} · {exemplo['pontuacao']} pontos",
            f"Preço {eur(exemplo['preco'])} (orçamento {eur(exemplo['orcamento'])}). Estoque: {estoque_exemplo}. "
            f"Pontuação {exemplo['pontuacao']}/100 = livro pedido {exemplo['pontos_livro_procurado']} + gênero "
            f"{exemplo['pontos_genero']} + tom {exemplo['pontos_tom']} + formato {exemplo['pontos_formato']} + "
            f"folga no orçamento {exemplo['pontos_preco']}.",
        ),
    ]


def escrever_markdown(respostas, gerado_em):
    linhas = [
        "# Readly Link — respostas às perguntas do cliente",
        "",
        f"Gerado automaticamente por `scripts/escrever_respostas.py` em {gerado_em}.",
        "Dados fictícios gerados para demonstração. Todos os números vêm dos marts do dbt.",
        "",
    ]
    for grupo, titulo in GRUPOS.items():
        linhas.append(f"## {titulo}")
        linhas.append("")
        for item in respostas:
            if item["grupo"] == grupo:
                linhas.append(f"### {item['id']}. {item['pergunta']}")
                linhas.append("")
                linhas.append(f"**{item['destaque']}** — {item['destaque_rotulo']}")
                linhas.append("")
                linhas.append(item["resposta"])
                linhas.append("")

    ARQUIVO_RESPOSTAS.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_RESPOSTAS.write_text("\n".join(linhas), encoding="utf-8")


def main():
    dados = json.loads(ARQUIVO_JSON.read_text(encoding="utf-8"))
    respostas = montar_respostas(dados)

    # A página também precisa dos textos fixos (rótulos, perguntas e regras).
    dados["respostas"] = respostas
    dados["rotulos_motivo"] = ROTULOS_MOTIVO
    dados["rotulos_acao"] = ROTULOS_ACAO
    dados["perguntas_vendedor"] = [
        {"pergunta": pergunta, "campo": campo, "motivo": motivo}
        for pergunta, campo, motivo in PERGUNTAS_VENDEDOR
    ]
    dados["regras_adequado"] = REGRAS_ADEQUADO
    dados["estoque_exemplo"] = texto_estoque(
        dados["exemplo"]["estoque"], dados["exemplo"]["estoque_ilimitado"]
    )

    ARQUIVO_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    escrever_markdown(respostas, dados["gerado_em"])
    print(f"Respostas às perguntas escritas em: {ARQUIVO_RESPOSTAS}")


if __name__ == "__main__":
    main()
