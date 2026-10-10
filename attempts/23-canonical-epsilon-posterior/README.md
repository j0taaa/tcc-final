# 23 — Posterior com transições vazias e proveniência de tokens

Investigação, **não conquista confirmada**. Preserva cópias independentes do
núcleo22 v6. A22 permanece intacta e seus resultados desfavoráveis são mantidos.
Não há treinamento, decoder completo novo nem comparação nativa com EPIC.

## Contrato e perguntas científicas

1. **Uso.** Receber as probabilidades completas de um passo de uma dLLM e um
quadro de tokens fixos/livres, e devolver a massa de JSON válido, as marginais
de TODOS os tokens originais e uma amostra conjunta exata. Isso permite
preencher estruturas recursivas sem truncar o vocabulário a topK nem trocar
condicionamento conjunto por validação independente de cada posição. A saída
serve a um controlador probabilístico; não garante o significado do JSON.
2. **Tamanho/novidade.** Inferência gramatical, remoção ponderada de epsilon,
circuitos de somas/produtos e diferenciação são antecedentes. Mohri2002 admite
explicitamente remoção sob demanda em autômatos acíclicos; Opedal2023 fornece
parsing ponderado eficiente. Portanto **não** reivindicamos novo princípio de
remoção de epsilon ou de parsing. A candidata é uma implementação utilizável
com vocabulário original completo, gramática recursiva, marginais, amostragem
e reutilização, com custo menor que alternativas competentes. Sua suficiência
acadêmica continua aberta; apenas acelerar uma codificação ruim não basta.
3. **Escolha/alternativas.** A22 representa cada fechamento de token como um
terminal artificial MARK e insere Skip na gramática. A23 põe esses pesos no
scanner, conservando um circuito das escolhas originais. Comparar com a melhor
inferência preditiva de pilhas, as variantes22 e remoção epsilon nas partições
global/por posição. Essas três representações são ablações do MESMO compiler
epsilon, não três invenções concorrentes. Escolher uma representação somente
no desenvolvimento e exigir ganho frente a TODOS os nove kernels exatos
anteriores, inclusive ambas as variantes locais. Não alegar exclusividade do
quociente local quando as outras variantes epsilon compartilham o benefício.
Critério: >=20% no custo total wall E CPU, sinal favorável
em toda repetição, ou capacidade adicional localizada com recursos iguais.
Rejeição compete separadamente para uma amostra, pois não entrega marginais.
4. **Matemática.** Cada caminho tem uma única divisão em blocos de transições
vazias seguidas por um terminal real. Computar o polinômio de cada bloco,
preservando folhas (posição, grupo), depois intersectar com a gramática não
ambígua. Esse argumento prova massa, marginais, lei da amostra e reuso sem
código. Pode eliminar trabalho artificial de Skip; NÃO prova superioridade
sobre parsing epsilon competente ou pilhas em toda entrada. A análise inclui
closures sob demanda, floresta, saída completa e aritmética em bits.
5. **Experimentos.** Os mesmos seis documentos de desenvolvimento e suas
probabilidades completas arquivadas, todos4/8/16 masks, todos os controles,
limites iguais e rotações. Não gerar casos favorecendo epsilon. Congelar
protocolo/código antes de qualquer timing23. Só se passar, escolher método e
capturar TODOS os cinco documentos elegíveis externos já pinados para uma
confirmação independente. Dados antigos vistos não são confirmação fresca.
6. **Custo/dLLM.** Contar preparação por quadro, conversão completa de
probabilidades, inside/outside, todas as marginais originais, amostra/validação
e forward compartilhado realmente medido. Tabela/modelo carregados são startup
de serviço explicitamente separado. Custos de closures pertencem à operação,
incluindo as closures que não chegam à raiz. Gramática fixa, EOS ausente.
Não inferir benefício na trajetória inteira ou acerto semântico deste passo.
7. **Objeção.** Um controle pode fazer a mesma remoção, usar fechamento de
arcos, ou resolver o problema mais barato por pilhas. Fornecer a otimização
também aos controles de partições; preservar perdas. Closures podem aumentar
o grafo/circuito e piorar custos. Se nenhum ganho sobreviver, preservar a
tentativa e descartá-la como protagonista. Uma aceleração sobre Skip sozinha
não satisfaz o usuário. FactorDLM pode representar a mesma eliminação, sem
que sua implementação publicada suporte esta aplicação exatamente.
8. **Artigo.** Faltam protótipo correto, revisão adversarial de bijeção/custo,
medições completas contra controles fortalecidos, confirmação independente
e avaliação de significância/novidade. Prova escrita não é Lean nem revisão
humana. Prioridade e publicação não estão estabelecidas.

Fontes primárias conferidas: [Mohri2002](https://research.google/pubs/generic-e-removal-and-input-e-normalization-algorithms-for-weighted-transducers/),
[Opedal2023](https://aclanthology.org/2023.acl-long.204/),
[Rivaud/Pachet2017](https://arxiv.org/abs/1711.10436),
[FactorDLM](https://arxiv.org/html/2609.32900v1).

## Preservação

`work/reference-origin.json` identifica os arquivos copiados. As referências
ficam dentro desta tentativa; nenhuma importa módulos mutáveis de22. Modelos,
capturas completas e caches permanecem fora do Git. Cada versão será congelada
com hashes completos antes de medições.


## Validação anterior a timings23

Seis testes pequenos independentes passam nas12 representações, incluindo
lei do RNG real por enumeração de decisões, aliases, UTF8 parcial, reuso/clamp/
remasking e tokens com zero sintaxe ou estruturas inteiras. Vazio em bytes é
recusado pelo adapter mantido; zero slots tem massa JSON zero. Esse último caso
revelou o bug do trimming de pilhas: o estado inicial retido era falsamente
feito aceitante. Corrigido em22/23; nenhum quadro antigo medido tem zero slots.

Oráculo full-V:288 comparações exatas (24 quadros com uma lacuna ×12 kernels),
1.206.192 candidatos originais reconhecidos por UTF8/Python JSON. Fixação das
outras lacunas ao documento foi explicitamente usada APENAS para permitir
enumeração de correção; não é um resultado de desempenho nem observação nova
sobre modelo. Evidence: work/evidence/full-vocabulary-oracle.json. Comando:
`.venv-live/bin/python -m attempts.23-canonical-epsilon-posterior.work.audit_full_rows
--capture .cache/a22-development-cuda-v1 --output <novo.json>`.

`make test`:65 verificações passam; `make check`: lint/tipos/upstream/integridade
passam; verificação de3683 artefatos históricos passa. Scanner/compilação têm
checks de prazo; o worker mede ainda o limite sobre a operação inteira. Nada
disso confirma vantagem/novidade. T4301 permanece pendente até medição e gate.
