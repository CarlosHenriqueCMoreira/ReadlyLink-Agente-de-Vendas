// Página visual da Readly Link.
// Lê business_metrics.json (gerado pelos scripts exportar_metricas.py e
// escrever_respostas.py) e preenche cada seção da página.

// Frase do painel do topo, conforme o maior motivo de abandono.
const MUDANCA_POR_MOTIVO = {
  preco_acima_do_orcamento: "Perguntar o orçamento antes de recomendar e nunca oferecer um livro acima dele.",
  recomendacao_nao_combinou: "Perguntar para quem é, gênero e tom, e não pular volume de saga.",
  nao_encontrou_continuacao: "Identificar o último volume lido e oferecer o seguinte.",
  livro_procurado_sem_estoque: "Oferecer o mesmo livro no outro formato e avisar da reposição.",
  abandono_no_checkout: "Retomar o checkout com um livro adequado.",
  apenas_pesquisando: "Guardar a sugestão e enviar um lembrete."
};

// ---------- formatação ----------

function numero(valor) {
  return Number(valor || 0).toLocaleString("pt-BR");
}

function percentual(valor) {
  return Number(valor || 0).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "%";
}

function euro(valor) {
  // pt-PT escreve "15,00 €", igual aos textos gerados em Python.
  return Number(valor || 0).toLocaleString("pt-PT", { style: "currency", currency: "EUR" });
}

// Coloca um texto dentro do elemento com esse seletor.
function escrever(seletor, texto) {
  document.querySelector(seletor).textContent = texto;
}

// Coloca HTML dentro do elemento com esse seletor.
// Os dados vêm do nosso próprio JSON, por isso podemos usar innerHTML.
function montar(seletor, html) {
  document.querySelector(seletor).innerHTML = html;
}

// ---------- seções ----------

function mostrarTopo(dados) {
  const principal = dados.motivos_abandono[0];
  escrever("#principal-percentual", percentual(principal.percentual_abandonos));
  escrever("#principal-rotulo", "dos abandonos: " + dados.rotulos_motivo[principal.motivo_abandono].toLowerCase() + ".");
  escrever("#principal-detalhe", `${numero(principal.atendimentos)} de ${numero(dados.totais.sem_compra)} atendimentos sem compra.`);
  escrever("#principal-mudanca", MUDANCA_POR_MOTIVO[principal.motivo_abandono]);
  escrever("#hero-selo", `Dados fictícios · ${numero(dados.qualidade.atendimentos)} atendimentos · calculado pelo dbt`);
  escrever("#total-sem-compra", numero(dados.totais.sem_compra));
}

// Cartões das 23 perguntas. Cada grade da página tem data-grupo="...".
function mostrarRespostas(respostas) {
  document.querySelectorAll("[data-grupo]").forEach(function (grade) {
    let html = "";
    for (const item of respostas) {
      if (item.grupo !== grade.dataset.grupo) continue;
      html += `
        <article class="answer-card" id="pergunta-${item.id}">
          <span class="answer-index">${String(item.id).padStart(2, "0")}</span>
          <h3>${item.pergunta}</h3>
          <p>${item.resposta}</p>
          <div class="answer-result">
            <strong>${item.destaque}</strong>
            <span>${item.destaque_rotulo}</span>
          </div>
        </article>`;
    }
    grade.innerHTML = html;
  });
}

// Texto da evidência que aparece embaixo de cada barra.
function evidencia(motivo) {
  switch (motivo.motivo_abandono) {
    case "preco_acima_do_orcamento":
      return numero(motivo.evidencia_preco_acima_orcamento) + " com preço acima do orçamento";
    case "recomendacao_nao_combinou":
      return `${numero(motivo.evidencia_recomendacao_inadequada)} com gênero, tom ou volume errado · ${numero(motivo.casos_presente)} presentes`;
    case "nao_encontrou_continuacao":
      return numero(motivo.evidencia_continuacao_nao_oferecida) + " sem o próximo volume oferecido";
    case "livro_procurado_sem_estoque":
      return numero(motivo.evidencia_procurado_indisponivel) + " com o título pedido indisponível";
    case "abandono_no_checkout":
      return "aceitaram o livro e saíram no pagamento";
    default:
      return "sem intenção de comprar agora";
  }
}

function mostrarAbandonos(dados) {
  let html = "";
  for (const motivo of dados.motivos_abandono) {
    const largura = Math.max(motivo.percentual_abandonos, 2);
    html += `
      <article class="bar-row">
        <div class="bar-heading">
          <strong>${dados.rotulos_motivo[motivo.motivo_abandono]}</strong>
          <span>${numero(motivo.atendimentos)} casos · ${percentual(motivo.percentual_abandonos)}</span>
        </div>
        <div class="bar-track"><span class="bar-fill" style="width: ${largura}%"></span></div>
        <small class="bar-evidence">Evidência: ${evidencia(motivo)}</small>
      </article>`;
  }
  montar("#lista-abandonos", html);
}

function mostrarFunil(funil) {
  let html = "";
  for (const etapa of funil) {
    const largura = Math.max(etapa.percentual_inicial, 8);
    const perdidos = etapa.perdidos_nesta_etapa
      ? `<small>−${numero(etapa.perdidos_nesta_etapa)} clientes nesta etapa</small>`
      : "";
    html += `
      <div class="funnel-row">
        <div class="funnel-label"><span>${etapa.etapa}</span>${perdidos}</div>
        <div class="funnel-bar" style="width: ${largura}%">
          <strong>${numero(etapa.quantidade)}</strong>
          <span>${percentual(etapa.percentual_inicial)}</span>
        </div>
      </div>`;
  }
  montar("#funil", html);
}

function mostrarAntesDepois(linhas) {
  let html = `
    <div class="compare-row compare-head">
      <span>Regra</span><span>Antes</span><span>Depois</span><span>Casos avaliados</span>
    </div>`;
  for (const linha of linhas) {
    html += `
      <div class="compare-row">
        <span class="compare-name">${linha.indicador}</span>
        <span class="compare-before"><strong>${percentual(linha.antes_percentual)}</strong><small>${numero(linha.antes)} casos</small></span>
        <span class="compare-after"><strong>${percentual(linha.depois_percentual)}</strong><small>${numero(linha.depois)} casos</small></span>
        <span class="compare-base">${numero(linha.base)}</span>
      </div>`;
  }
  montar("#tabela-antes-depois", html);
}

function mostrarSolucoes(dados) {
  // Exemplo de solução de cada motivo, para achar pelo nome do motivo.
  const exemplos = {};
  for (const exemplo of dados.exemplos_solucoes) {
    exemplos[exemplo.motivo_abandono] = exemplo;
  }

  let html = "";
  for (const resultado of dados.resultados_solucoes) {
    const exemplo = exemplos[resultado.motivo_abandono];

    let acoes = "";
    for (const acao of resultado.acoes_utilizadas.split(", ")) {
      acoes += `<li>${dados.rotulos_acao[acao]}</li>`;
    }

    let textoExemplo = "";
    if (exemplo) {
      textoExemplo = `<small class="solution-example">Exemplo ${exemplo.atendimento_id}: ${exemplo.titulo_solucao} · ${exemplo.formato_solucao.toLowerCase()} · ${euro(exemplo.preco_solucao)} (orçamento ${euro(exemplo.orcamento)})</small>`;
    }

    html += `
      <article class="solution-card">
        <span class="solution-problem">${dados.rotulos_motivo[resultado.motivo_abandono]}</span>
        <h3>${numero(resultado.casos_com_solucao)} de ${numero(resultado.casos_encontrados)} casos receberam uma ação</h3>
        <ul class="solution-actions">${acoes}</ul>
        <div class="solution-progress"><span style="width: ${resultado.cobertura_percentual}%"></span></div>
        <div class="solution-footer">
          <strong>${percentual(resultado.cobertura_percentual)} cobertos</strong>
          <span>${numero(resultado.casos_para_revisao_humana)} para revisão humana</span>
        </div>
        ${textoExemplo}
      </article>`;
  }
  montar("#resultados-solucoes", html);

  const contagens = dados.contagens_solucoes;
  escrever("#solucoes-geradas", numero(contagens.automaticas));
  escrever("#solucoes-cobertura", percentual((100 * contagens.automaticas) / dados.totais.sem_compra));
  escrever("#solucoes-revisao", numero(contagens.revisao_humana));
}

function mostrarVendedor(dados) {
  let perguntas = "";
  dados.perguntas_vendedor.forEach(function (item, posicao) {
    perguntas += `
      <li>
        <span>${posicao + 1}</span>
        <div>
          <strong>${item.pergunta}</strong>
          <p>${item.motivo}</p>
          <code class="field-tag">${item.campo}</code>
        </div>
      </li>`;
  });
  montar("#perguntas-vendedor", perguntas);

  let regras = "";
  for (const regra of dados.regras_adequado) {
    regras += `<li>${regra}</li>`;
  }
  montar("#regras-adequado", regras);
}

function mostrarExemplo(exemplo, estoque) {
  const iniciais = exemplo.nome_completo.split(" ").slice(0, 2).map((parte) => parte[0]).join("");
  escrever("#iniciais-cliente", iniciais);
  escrever("#nome-cliente", exemplo.nome_completo);
  escrever("#atendimento-cliente", exemplo.atendimento_id);

  montar("#dados-cliente", `
    <div><span>Pedido</span><strong>Continuar a saga ${exemplo.ultima_saga}</strong></div>
    <div><span>Último volume lido</span><strong>Volume ${exemplo.ultimo_volume_lido}</strong></div>
    <div><span>Gênero e tom</span><strong>${exemplo.genero_desejado} · ${exemplo.tom_desejado}</strong></div>
    <div><span>Formato</span><strong>${exemplo.formato_desejado.toLowerCase()}</strong></div>
    <div><span>Orçamento</span><strong>${euro(exemplo.orcamento)}</strong></div>`);

  escrever("#livro-recomendado", `${exemplo.titulo} · ${exemplo.saga}, volume ${exemplo.volume}`);
  escrever("#motivo-recomendacao", exemplo.justificativa);
  escrever("#preco-recomendado", euro(exemplo.preco));
  escrever("#estoque-recomendado", estoque);
  escrever("#pontos-recomendacao", exemplo.pontuacao + " / 100 pontos");

  // Barras da pontuação: [nome, pontos que o livro recebeu, máximo possível]
  const partes = [
    ["Livro pedido", exemplo.pontos_livro_procurado, 30],
    ["Gênero", exemplo.pontos_genero, 30],
    ["Tom", exemplo.pontos_tom, 15],
    ["Formato", exemplo.pontos_formato, 15],
    ["Folga no orçamento", exemplo.pontos_preco, 10]
  ];
  let barras = "";
  for (const [nome, pontos, maximo] of partes) {
    barras += `
      <div class="score-row">
        <span>${nome}</span>
        <div class="score-track"><span style="width: ${(100 * pontos) / maximo}%"></span></div>
        <strong>${pontos}/${maximo}</strong>
      </div>`;
  }
  montar("#pontos-detalhe", barras);

  const pulouVolumes = exemplo.volume_antes > exemplo.ultimo_volume_lido + 1;
  escrever(
    "#antes-recomendacao",
    `Antes: o agente antigo ofereceu «${exemplo.titulo_antes}» (volume ${exemplo.volume_antes}, ${euro(exemplo.preco_antes)})` +
      (pulouVolumes ? ", pulando volumes da saga," : "") +
      " e a cliente saiu sem comprar."
  );
}

// ---------- início ----------

async function carregarDados() {
  try {
    const resposta = await fetch("business_metrics.json");
    const dados = await resposta.json();

    mostrarTopo(dados);
    mostrarRespostas(dados.respostas);
    mostrarAbandonos(dados);
    mostrarFunil(dados.funil);
    mostrarAntesDepois(dados.antes_depois);
    mostrarSolucoes(dados);
    mostrarVendedor(dados);
    mostrarExemplo(dados.exemplo, dados.estoque_exemplo);

    const geradoEm = new Date(dados.gerado_em);
    escrever("#data-atualizacao", "Atualizado em " + geradoEm.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }));
  } catch (erro) {
    escrever("#data-atualizacao", "Não foi possível carregar as métricas");
    escrever("#principal-rotulo", "Execute ./scripts/gerar_documentacao.sh para gerar os dados.");
    console.error(erro);
  }
}

carregarDados();
