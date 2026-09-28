# M23 — comparação com EPIC no domínio M22

Protocolo congelado antes das medições. O pedido do usuário exige comparação
com o EPIC real; o guloso do M22 nunca deve receber esse nome.

## Contrato e coorte

Reusar integralmente os 100 pedidos M22, sem seleção por resultado. Isso é uma
comparação adicional em uma coorte já conhecida, não nova confirmação independente.
Modelo, tokenizer/revisão, NF4, GPU, prompt, preservação de operandos, 24 slots,
limite de 24 forwards e 120 s por geração são mantidos. Gabarito só no avaliador.
Piloto: cinco primeiros pedidos, sem ajuste por acurácia. Confirmação: todos os
100 pedidos, cinco métodos, ordem rotativa por tarefa; repetição em ordem inversa.

## Métodos e assimetrias

- `exact`: MWPC Rust M22, probabilidades do vocabulário completo, domínios
  posicionais e gramática byte CFG, até 24 propostas por forward, mesma conclusão
  e fallback certificado do M22.
- `epic_native_1`, `epic_native_4`: gerador LLaDA original do commit EPIC
  `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, com vocabulário nativo; respectivamente
  1 e 4 etapas programadas (24 ou 6 transferências na primeira etapa), até 100
  rejeições. Regular cover, verificação exata do lote, DFA-free checker e caches
  ativados. Reamostragem e conclusão EOS do upstream são preservadas.
- `epic_domains_1`, `epic_domains_4`: mesmo gerador, logits mascarados para os
  domínios posicionais M22. **A máscara renormaliza a confiança**, portanto é um
  controle de domínio adicional, não isolamento perfeito do seletor MWPC.

A gramática exportada contém as mesmas produções byte-CNF e reconhece as mesmas
strings, com lexemas de um byte. O símbolo inicial vem primeiro, como exige o
leitor de regular cover do upstream; `to_normal_form()` prepara o cache do parser.
Esses são cuidados de integração, sem alteração no código vendorizado.
A escolha de lexemas por byte acompanha a representação do MWPC e não demonstra
que esta seja a representação mais eficiente possível para EPIC.

O EPIC usa lacunas abstratas nas consultas de viabilidade; mesmo sua variante
com logits mascarados não tem o contrato de conclusão nos domínios finitos do
MWPC. EPIC pode tentar várias alternativas no mesmo forward e terminar em EOS
preenchendo a cauda; MWPC faz novas inferências depois de aceitar o conjunto.
Não atribuir diferenças finais exclusivamente à optimalidade de seleção.
Não há reparo posterior nem infilling externo adicionado a nenhum método.

## Instrumentação e verificações

Hooks só observam o seletor e `check_valid` originais, sem substituir decisões;
contar lotes tentados/selecionados e erros que o upstream intercepta. Registrar
eventos de canvas, rejeições, forwards reais, status, saída e correção exata da
chamada. Modelo observado sincroniza CUDA e mede forwards; tempos de seleção,
checagem serial e máscara de domínio são separados. Parsing/backtracking são
internos ao upstream e não separáveis por esses hooks. Registrar custo de setup
separado e incluí-lo no tempo total reportado; excluir carregamento/warmup e a
consulta contrafactual do MWPC. Não comparar tempos de hardware distintos.

Testes CPU anteriores ao piloto: equivalência de linguagem em domínio exaustivo,
execução efetiva do seletor de lotes original, preservação dos hooks/env e coorte.
Congelar fonte/config em commit limpo. Arquivar todos os resultados, inclusive
falhas; gerar tabelas via script com hashes e verificação semântica dos outputs.
Métrica principal: chamada exata correta. Secundárias: validade na linguagem
permitida, forwards, tempo total e pares de sucesso/derrota. Repetições não são
novas tarefas. Nenhuma superioridade é pressuposta.
