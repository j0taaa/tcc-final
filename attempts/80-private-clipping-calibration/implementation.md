# A80 — implementação e correções anteriores aos dados

O protocolo e a prova foram congelados em `d356cfde101ee27e626909d9618f419769cd7af7`.
Este registro resolve os dois apontamentos da revisão independente pré-dados,
sem sobrescrever aqueles arquivos. Não houve execução dos casos de produção ou
medição científica antes dessas correções. Casos, seeds, orçamentos e gate
continuam os mesmos. Revisão de subagente não é revisão humana.

## Custo comparado

A primeira implementação do runner colocava a verificação enumerável depois da
primeira saída. Isso deixava esse trabalho fora do tempo usado pelo gate nos
métodos amostrais, embora a enumeração fosse necessária antes da saída do
controle exato. Não há medição dessa implementação nem ganho atribuído a ela.

Na versão produtora, a verificação obrigatória de massa, projeção e diagnóstico
KL dos casos enumeráveis ocorre **antes da primeira saída de todos os métodos**.
O gate usa o tempo desde o lançamento do subprocesso até essa primeira palavra
validada: inclui imports, compilação, preparo, precheck, todas as palavras de
calibração, solução, certificados, métricas de payload, verificação enumerável e
emissão. O limiar do método amostral não é substituído pelo ótimo encontrado no
diagnóstico. As outras 15 palavras têm custo registrado separadamente. O pico
RSS e o limite de parede cobrem o processo inteiro.

A verificação enumerável não atribui ao PRNG uma garantia estatística ou privada.
Os logaritmos KL de diagnóstico são binary64, sem certificação por intervalos.
O controle exato vem depois dos cinco métodos rotacionados em cada configuração.

## Bits e memória

A primeira implementação confundia a largura máxima de um numerador/denominador
com seu payload somado e observava apenas racionais já reduzidos na emissão e
no controle exato. Isso omitia produtos intermediários. A versão produtora usa:

- Payload lógico: soma os comprimentos dos **dois** inteiros de cada racional.
  Entradas repetidas contam repetidamente; storage Python conta objetos únicos.
- Controle exato: para `L=lcm(denominadores de P e mu)` e
  `B=bits(L)+bits(RN)+bits(RD)+2`, registra `8B` como **majorante**, não como
  largura observada. Os coeficientes dos trechos têm denominadores que dividem
  `L*RD`, interceptos que dividem `L`, inclinação entre zero e `R`, e intercepto
  entre zero e um. Raízes e eventos usam produtos de até dois desses
  denominadores; comparações e adições antes do gcd duplicam novamente suas
  larguras. O fator oito cobre esses produtos, somas, eventos, raiz e testemunho
  de normalização. Usa-se a normalização das leis, não uma hipótese de custo
  unitário. O máximo interno do algoritmo de multiplicação/gcd Python não é
  observado.
- Emissão: se `B` limita numeradores e denominadores de `a,R,P(y),mu(y)`,
  registra `16(B+1)` como majorante dos operandos racionais, inclusive produtos
  anteriores à redução. Os termos do envelope usam até quatro larguras; sua
  divisão pelo clipping usa até sete; o fator dezesseis cobre comparações,
  somas e decisão Bernoulli. O sampler e avaliador da fonte têm métricas
  separadas. O máximo entre propostas não cresce com a quantidade de rejeições.

O payload do controle exato refere-se aos IDs e às leis enumeradas retidas; não
observa o workspace do sweep liberado ao retornar. O pico RSS inclui esse
workspace. Os métodos amostrais declaram seu próprio estado retido e workspace
vivo. Essas métricas não são intercambiáveis, e não fundamentam superioridade
global de memória. Nenhuma delas é VRAM. Nos caminhos de precheck que emitem `P`
diretamente, o estado adicional de calibração é zero; o preparo continua pago.

Regressões pequenas verificam a distinção: em `P=(1/100,99/100)`,
`mu=(1/3,2/3)`, são 29 bits somente nos numeradores e denominadores das leis,
e o sweep pode manipular `297/400` (9 bits). Na emissão,
`(1/2)*(1/3)=1/6` precisa de 3 bits no denominador.

## Reprodução

Depois do commit produtor, com a árvore de fontes congelada:

```bash
.venv/bin/python -m unittest discover -s attempts/80-private-clipping-calibration -v
.venv/bin/python -m attempts.80-private-clipping-calibration.run \
  --output attempts/80-private-clipping-calibration/work/evidence/offline-v1
```

O runner recusa sobrescrever o diretório de saída e verifica que suas fontes
estão commitadas. O limite global é 900 segundos, sem repetição seletiva. Não há
modelo, treinamento, GPU ou alegação de utilidade semântica neste ensaio.
