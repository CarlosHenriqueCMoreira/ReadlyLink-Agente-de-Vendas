# Readly Link — respostas às perguntas do cliente

Gerado automaticamente por `scripts/escrever_respostas.py` em 2026-09-29T02:30:11+01:00.
Dados fictícios gerados para demonstração. Todos os números vêm dos marts do dbt.

## Diagnóstico

### 1. O que está impedindo o cliente de comprar?

**61,2%** — dos atendimentos terminam sem compra

1.468 de 2.400 atendimentos terminaram sem compra. As três maiores causas são recomendação não combinou (461), preço acima do orçamento (451), não encontrou a continuação da saga (295), que juntas somam 82,2% dos abandonos. As três vêm do atendimento antigo: recomendar sem perguntar o orçamento, ignorar o gosto de quem vai ler e errar o volume da saga.

### 2. A Readly Link entende o que a pessoa quer ler?

**9,6% → 94,3%** — presentes no gênero de quem recebe (antes → depois)

Só em parte. O agente antigo usava o gênero mais lido do histórico e ignorava o tom pedido e quem ia receber o presente: 68,2% das recomendações respeitavam o tom pedido e só 9,6% dos presentes eram do gênero de quem recebe. Com as cinco perguntas novas (para quem, gênero, tom, formato e orçamento), o tom passa para 88,9% e os presentes para 94,3%. Os 1.000 clientes têm perfil de leitura calculado a partir do histórico.

### 3. A recomendação de livros está funcionando?

**37,9% → 93,9%** — recomendações que cumprem todas as regras

Não. Só 37,9% das recomendações antigas cumpriam todas as regras de livro adequado: 657 estavam acima do orçamento e 1.172 pulavam volume de saga. A aceitação foi de 44,1%. Com o motor de regras, 93,9% dos atendimentos recebem um livro adequado. Os restantes não têm opção que cumpra as regras e vão para um vendedor.

### 4. O estoque ainda faz a empresa perder vendas?

**18** — vendas perdidas por falta de estoque

Pouco, mas perde. 18 abandonos (1,2%) aconteceram porque o título pedido estava sem estoque no formato escolhido. 8 dos 48 livros físicos estão esgotados. O agente antigo não inventava estoque (0 divergências de preço e 0 produtos indisponíveis recomendados). O que faltava era oferecer o mesmo livro no formato digital.

### 5. A venda chega até o fim?

**38,8%** — de conversão

Em 38,8% dos casos. De 2.400 atendimentos, 2.087 passaram da busca, 1.059 aceitaram a recomendação e foram ao checkout e 932 concluíram a compra. A maior perda está na recomendação (1.028 clientes). No checkout saem 127.

### 6. Como o atendimento funciona atualmente e onde ele falha?

**1.028** — clientes perdidos na etapa de recomendação

O cliente diz o que procura e o agente recomenda um livro usando só o gênero mais lido, a saga e o estoque. Não pergunta o orçamento, o tom nem para quem é. Falha em três pontos: na busca (313 não encontraram a continuação ou o título), na recomendação (1.028 recusaram pelo preço, por não combinar ou só estavam pesquisando) e no checkout (127).

### 7. Por que os clientes abandonam a compra?

**31,4%** — recomendação não combinou

Recomendação não combinou: 461 (31,4%) — todos receberam um livro de outro gênero, outro tom ou que pulava volume; 264 eram presentes. Preço acima do orçamento: 451 (30,7%) — em todos o preço era maior que o orçamento, em média 6,64 € acima. Não encontrou a continuação da saga: 295 (20,1%) — em todos o agente não ofereceu o próximo volume da saga. Abandono no checkout: 127 (8,7%) — aceitaram o livro e saíram no pagamento. Cliente estava apenas pesquisando: 116 (7,9%) — viram a recomendação sem intenção de comprar agora. Livro procurado sem estoque: 18 (1,2%) — em todos o título pedido estava indisponível no formato escolhido.

### 8. O que estava ruim e o que a solução mudou?

**72,6% → 93,9%** — recomendações dentro do orçamento

Nos mesmos 2.400 atendimentos: dentro do orçamento 72,6% → 93,9%; gênero pedido 82,8% → 93,9%; tom pedido 68,2% → 88,9%; sem pular volume 51,2% → 89,2%; próximo volume certo 71,1% → 100,0%; título procurado oferecido 92,0% → 100,0%; presentes no gênero de quem recebe 9,6% → 94,3%; livro adequado 37,9% → 93,9%. Isto mede o cumprimento das regras. O efeito nas vendas só pode ser medido depois que o novo atendimento estiver em produção.

## Soluções produzidas pelo sistema

### 9. Que solução o sistema produziu para os clientes com orçamento insuficiente?

**362/451** — receberam uma opção dentro do orçamento

Para os 451 clientes que recusaram pelo preço, o sistema procura um livro adequado que caiba no orçamento. Primeiro tenta o mesmo livro no outro formato (o digital custa cerca de 10 € menos) e depois outro título do gênero pedido. 362 (80,3%) receberam uma opção, com preço médio de 15,28 € para um orçamento médio de 18,63 €. 89 vão para revisão humana porque nenhum livro adequado cabe no orçamento. Exemplo (ATD-001272): orçamento de 27,99 €; antes foi oferecido «A Última Página do Verão» por 28,50 €; agora o sistema oferece «O Caderno de Inverno» (digital, 12,40 €).

### 10. Que solução foi produzida para recomendações que não combinaram?

**449/461** — receberam uma nova recomendação

O sistema refaz a recomendação com as regras novas: gênero e tom pedidos, sem pular volume, dentro do orçamento, ainda não lido e, de preferência, de outra saga. Em presentes usa o gosto de quem vai receber. 449 de 461 receberam um livro novo e 12 vão para revisão. Exemplo (ATD-001694): orçamento de 45,86 €; antes foi oferecido «O Reino de Cinzas» por 21,10 €; agora o sistema oferece «A Torre do Amanhecer» (digital, 18,05 €).

### 11. Como o sistema trata clientes que abandonaram o checkout?

**122/127** — com checkout retomado

Retoma o checkout. Se o livro escolhido ainda cumpre as regras, o cliente recebe o mesmo carrinho (80 casos). Se o livro estava acima do orçamento ou pulava volume, recebe uma opção adequada (42 casos). 5 vão para revisão.

### 12. Como o sistema trata clientes que estavam apenas pesquisando?

**113/116** — com lista guardada e lembrete

Não força a venda. Guarda uma lista com a melhor sugestão adequada e envia um lembrete depois. Se o livro visto já cumpria as regras, fica o mesmo (75). Se não, é trocado por um adequado (38). 3 vão para revisão.

### 13. Como o sistema ajuda quem não encontrou a continuação de uma saga?

**199/295** — receberam o próximo volume ou uma saga semelhante

Identifica a última saga lida e o último volume. 86 clientes recebem o próximo volume, no formato que cabe no orçamento. 113 já tinham terminado a saga (não existe continuação) e recebem o volume 1 de uma saga do mesmo gênero ou tom. 96 vão para revisão: 26 porque o próximo volume não cabe no orçamento e 70 porque não há saga semelhante disponível.

### 14. O que o sistema oferece quando o livro procurado está sem estoque?

**17/18** — receberam uma alternativa

Primeiro, o mesmo livro no outro formato (15 casos). Se não couber no orçamento, um livro semelhante do mesmo gênero (2). Nos dois casos o cliente é avisado quando o físico voltar ao estoque. 1 vai para revisão. Exemplo (ATD-000251): o cliente procurava «O Segredo das Acácias» em físico, que está esgotado; agora recebe «O Segredo das Acácias» em digital por 10,65 € (orçamento 44,46 €).

### 15. Quantos casos receberam uma solução automática?

**1.262** — de 1.468 abandonos (86,0%)

1.262 de 1.468 atendimentos sem compra (86,0%). 155 têm ação pronta (o livro original já cumpria as regras) e 1.107 receberam uma alternativa. Todas passam nos testes automáticos: livro disponível, dentro do orçamento, ainda não lido e sem pular volume.

### 16. Quantos casos precisam de revisão humana?

**206** — casos (14,0% dos abandonos)

206 (14,0%). Nenhum livro adequado cabe no orçamento declarado: 89; Não há saga semelhante adequada disponível: 70; O próximo volume não cabe no orçamento em nenhum formato: 26; Nenhuma alternativa cumpre todas as regras: 21. Nestes casos nenhum livro cumpre todas as regras, e o sistema não inventa uma alternativa.

## Método do vendedor

### 17. Que perguntas o vendedor deve fazer antes de recomendar?

**5** — perguntas, cada uma ligada a uma regra

1. É para você ou para presente? (Define quem vai ler. Em presentes o histórico de quem compra não é usado.) 2. Que gênero você quer ler agora? (O pedido de hoje pesa mais do que o gênero mais lido no passado.) 3. Que tom de leitura procura (épico, leve, emocional, intrigante...)? (Evita um livro do gênero certo com a atmosfera errada.) 4. Prefere físico ou digital? (Define a oferta e a disponibilidade. O digital é sempre disponível e mais barato.) 5. Qual é o orçamento máximo? (Nenhuma recomendação pode passar deste valor.)

### 18. O que torna um livro adequado para o cliente?

**5** — regras verificadas em todos os atendimentos

Um livro é adequado quando cumpre as cinco regras: está disponível no formato oferecido (o digital é sempre disponível); cabe no orçamento declarado pelo cliente; o cliente ainda não leu (em presentes, o histórico de quem compra não conta); respeita a ordem da saga: volume 1 ou o volume anterior já foi lido (presentes: só volume 1); é do gênero pedido, ou é exatamente o livro que o cliente pediu pelo nome.

### 19. O que torna um livro inadequado?

**1.490** — recomendações antigas inadequadas

Violar qualquer uma das regras: estar acima do orçamento, ser de outro gênero, pular um volume da saga, repetir um livro já lido ou estar indisponível. No atendimento antigo: 657 acima do orçamento, 412 de outro gênero, 1.172 pulavam volume e 763 tinham outro tom. Tom diferente reduz a pontuação, mas sozinho não elimina o livro.

### 20. Como o vendedor consegue explicar e justificar uma recomendação?

**100** — pontos divididos por regra

Cada recomendação traz uma pontuação de 0 a 100 dividida por critério (livro pedido 30, gênero 30, tom 15, formato 15, folga no orçamento até 10) e uma frase gerada com os dados do cliente. Exemplo: «é o próximo volume da saga As Torres de Âmbar (volume 2); é do gênero pedido (Fantasia); tem o tom pedido (épico); está no formato pedido (digital); cabe no orçamento (15,00 € de 43,20 €); o cliente ainda não leu».

## Exemplo explicável

### 21. Qual livro foi recomendado no exemplo?

**O Vale das Lanternas** — As Torres de Âmbar · volume 2

«O Vale das Lanternas», volume 2 da saga As Torres de Âmbar, em formato digital, para Débora Pereira Rocha (ATD-001684). Antes, o agente antigo tinha oferecido «O Reino de Cinzas» (volume 4), e a cliente saiu sem comprar porque não encontrou a continuação.

### 22. Quais dados do cliente levaram a essa recomendação?

**vol. 1 → 2** — último volume lido de As Torres de Âmbar

Pedido: «Quero continuar uma saga que comecei, mas não sei qual é o próximo volume.» Para: a própria cliente. Gênero Fantasia, tom épico, formato digital, orçamento 43,20 €. Histórico: 3 livros lidos, última saga As Torres de Âmbar até o volume 1, gênero preferido Romance e formato preferido digital.

### 23. Qual é o preço, estoque e pontuação do livro recomendado?

**15,00 €** — Digital · sempre disponível · 97 pontos

Preço 15,00 € (orçamento 43,20 €). Estoque: Digital · sempre disponível. Pontuação 97/100 = livro pedido 30 + gênero 30 + tom 15 + formato 15 + folga no orçamento 7.
