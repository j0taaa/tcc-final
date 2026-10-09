# Resultado da auditoria independente PL

Gerado por `work/report.py` a partir de todos os registros. A nota original e
as versões desfavoráveis permanecem preservadas. A amostragem condicional
e a vantagem matemática delimitada são verificáveis; novidade/publicação
e benefício em treinamento neural continuam sem confirmação.

## Correção

- 1151 eventos, 2939 caminhos originais e 0 divergências racionais.
- 48 casos de score completo/covariância.
- Redução com uma réplica iid nos oráculos: 0.00% a 19.89%, mediana 4.33%. São fixtures, não treinamento.
- Omitir o score latente introduziu viés em 48 casos.
- Enumeração independente, integração das decisões categóricas e reconhecedor JSON.
- Não é prova integral do Python/Rust, resultado Lean novo ou revisão humana.

## Todos os replays de modelo

| Versão | Método | Lotes 16 completos | Inconclusivos | Fora do teto de enumeração |
|---|---|---:|---:|---:|
| reference-replay | certified_tangent_mixture | 124 | 20 | 0 |
| reference-replay | enumeration | 78 | 6 | 60 |
| reference-replay | rejection_with_f_L_envelope | 141 | 3 | 0 |
| dyadic-replay | certified_tangent_mixture | 137 | 7 | 0 |
| dyadic-replay | enumeration | 78 | 6 | 60 |
| dyadic-replay | rejection_with_f_L_envelope | 141 | 3 | 0 |
| tight-replay | certified_tangent_mixture | 138 | 6 | 0 |
| tight-replay | enumeration | 78 | 6 | 60 |
| tight-replay | rejection_with_f_L_envelope | 141 | 3 | 0 |
| final-control-replay | certified_tangent_mixture | 138 | 6 | 0 |
| final-control-replay | enumeration | 78 | 6 | 60 |
| final-control-replay | rejection_with_f_L_envelope | 141 | 3 | 0 |
| final-control-replay | single_tilt_rejection | 144 | 0 | 0 |

Os nove inputs originais foram mantidos; oito compilaram, gerando 48
eventos PL nativos. Uma preparação foi recusada pelo orçamento de células.
Cada método tem três repetições por evento; preparação 30 s, amostragem
cumulativa 10 s, enumeração no máximo um milhão de combinações.
Os inputs já foram usados no desenvolvimento: não são avaliação externa nova.

Prefixos concluídos após o deadline cooperativo: 2 nos quatro registros; os detalhes estão no JSON, sem descartá-los.

## Comparação exata de tentativas

`E[N]=normalizador_proposta/Z_alvo`; a razão cancela o alvo.
Normalizadores racionais em hexadecimal estão nos registros originais.

| Controle | Eventos comparáveis | Mistura com menos tentativas esperadas | Mediana controle/mistura |
|---|---:|---:|---:|
| rejection_with_f_L_envelope | 48 | 10 | 0.715703 |
| single_tilt_rejection | 48 | 1 | 0.310522 |

A inclinação única usa o majorante secante ótimo de sua família, com taxa
aproximada em 80 dígitos e rejeição racional exata. A diferença de tentativas
não inclui preparação e não implica vantagem de tempo.

## Custo completo da consulta contra o melhor controle registrado

| Lote | Eventos pareados | Mistura mais rápida | Só mistura concluiu | Só controle concluiu |
|---|---:|---:|---:|---:|
| 1 | 48 | 0 | 0 | 0 |
| 4 | 47 | 0 | 0 | 1 |
| 16 | 46 | 0 | 0 | 2 |

Escolher o melhor controle entre versões é um controle otimista de
diagnóstico, não um seletor implementado. Usa mediana das três repetições
somente quando todas concluíram aquele prefixo. Timeouts permanecem censurados.
O custo inclui preparação condicional; a compilação comum é publicada
separadamente. Enumeração independente não requer essa compilação.
Forward, backward e recompensa não foram executados.

## O que a matemática sustenta

A redução condicional PL, o envelope fatorável racional e o limite de
tentativas estão em [mathematical-review.md](mathematical-review.md).
A prova escrita [product-proposal-separation.md](product-proposal-separation.md)
mostra uma família JSON em que **qualquer proposta produto única** precisa
de esperança pelo menos `exp(m/360)/3`, contra `O(sqrt(m))` da mistura.
A família é objeto de prova; um contador especializado também é polinomial.
Não há alegação contra todos os solvers nem exclusividade do benefício.

A identidade de Rao-Blackwellização garante redução de variância quando
há ruído latente; ela é antecedente conhecido. Ganho por tempo exige que
a redução supere o custo adicional, que este replay não mede em treinamento.
A política deve registrar a seleção PL e incluir seu score/normalização.
Não há justificativa automática para clipping PPO/GRPO.

Há uma objeção adicional em [auxiliary-variable-objection.md](auxiliary-variable-objection.md):
um passo Gibbs com auxiliares PL pode iniciar na proposta original já
em estacionariedade, gerando uma réplica correlacionada sem viés e
com variância não maior. Não foi implementado ou medido. Réplicas iid
não são obrigatórias para reduzir variância; esse controle deve entrar
na avaliação de treinamento antes de reivindicar vantagem de aplicação.

## Decisão científica

Confirmado nesta auditoria: consistência exata nas instâncias verificadas
e prova escrita de uma vantagem assintótica contra uma classe precisa.
Não confirmado: prioridade/significância acadêmica própria, redução de
custo neural total, melhoria de geração ou treinamento de uma dLLM.
Portanto isto não autoriza anunciar que todos os requisitos do TCC
foram atendidos. O próximo gate é anterioridade do kernel/limite e
benefício por custo em uma política on-policy real contra esse controle,
não mais exemplos
escolhidos para mostrar JSON válido.
