# Antecedentes adicionais conferidos na decisão de utilidade

Complemento da matriz do README; não reivindica prioridade nem avaliação humana.
A operação continua sendo o posterior de propostas descartadas após commitments
PL em uma predição gramatical da dLLM, sem alterar a política executada.

- [Sakhi, Rohde e Chopin (2023)](https://arxiv.org/html/2308.01566v2),
  §2.2 e Apêndice A.1: discutem custo/variância de gradientes de políticas
  Plackett–Luce, rejeição e propostas especializadas. O método principal troca
  a política por perturbações latentes. Isso é antecedente da motivação de
  eficiência estatística, não uma implementação do nosso posterior CFG de
  tokens descartados. Não atribuir a nós a descoberta de que scores PL podem
  ter muita variância, nem comparar políticas diferentes como se fossem iguais.
- [Jolly e Xavier (2026)](https://arxiv.org/html/2607.11146v1), §§4–5 e 8:
  reutilizam um pool de itens/gerações para uma recompensa best-of-K mediante
  condicionamento por rank/threshold e Horvitz–Thompson. A redução combinatória
  é exata; a implementação com Q nós de quadratura é numérica e não fornece
  limite uniforme de erro finito. Isso não é o nosso contrato de tokens
  descartados dado o canvas e a ordem de posições. A diferença de contrato
  também impede anunciar que nosso sampler melhora esse estimador sem derivar
  outra redução. Não são baselines de latência desta operação.
- [Dusart (2010)](https://arxiv.org/pdf/1002.0442), Teorema 5.2, p. 4:
  o limite explícito de theta usado na nova obstrução é antecedente matemático,
  não resultado do TCC. A prova própria aplica esse limite ao denominador de
  uma família PL com lambda=q e separa os contratos escrever uma fração exata
  e produzir amostras exatas. A rejeição simples vence nessa família.

O ganho de réplicas/Rao–Blackwellização, MH independente e aproximação positiva
por exponenciais é conhecido. O candidato específico é a construção racional
certificada para este posterior sobre o circuito, com custo em bits, separação
contra uma proposta produto única e uma aplicação delimitada. Os novos estudos
não fecham sozinhos a anterioridade nem a significância para publicação.
