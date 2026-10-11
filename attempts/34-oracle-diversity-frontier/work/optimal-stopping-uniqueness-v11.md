# Uma fronteira exata exige cauda não limitada: caracterização escrita

2026-10-11. Refinamento matemático, depois dos DOIS screens negativos; não
é nova captura, correção deles, uso confirmado ou reivindicação de prioridade.
Score e caracterização de eficiência sequencial são antecedentes de DeGroot.
O argumento abaixo especializa o contrato A34 para outputs retidos, e precisa
ser confrontado com a literatura antes de apresentar sua especialização nova.

## Contrato e enunciado

Use o oráculo de `theory-v1.md` e o budget uniforme de
`uniform-budget-score-v11.md`; cauda exponencial não é mais necessária.
Seja r um inteiro>=3. O
algoritmo retém LITERALMENTE o primeiro bit B1 como X, tem sup_p E_p N<=r,
e atinge inf_p eta(p)>=1-2/r. Pode usar aleatoriedade auxiliar, inventar Y e
adaptar a parada; não precisa inicialmente ser um random walk.

Então, quase certamente para TODO0<p<1, sua parada e segundo output são:

    tau = primeira volta do signed walk M_n=2S_n-n a0,
          OU primeiro encontro de r*sign(M_1);
    N=tau,  Y é o último bit observado em tau.

Logo, entre esse contrato de retenção e trabalho minimax ótimo, não há outro
sampler com cauda deterministicamente limitada. Nenhum cap finito consegue
atingir exatamente1-2/r mantendo sup_p E N<=r. Isso NÃO exclui samplers
aproximadamente ótimos, orçamento maior, informação sobre p ou outras saídas.

## Prova

No ponto justo p1/2, seja Z=X+Y-1, s=P(Z!=0). A fronteira A34 força s=1/r:
eta>=1-2/r exige s<=1/r, enquanto o lower bound exige s>=1/r. O score fornece
E[ZM]=1 e E M²=E N. A desigualdade inteira com k=r-1 dá

    E N >= 2r-1-r(r-1)s = r.

O budget dá E N<=r, portanto todas as desigualdades têm igualdade. Em Z0,
o termo descartado M² precisa ser0. Em Z!=0, o termo não negativo
(ZM-r+1)(ZM-r) precisa ser0, portanto ZM é r-1 ou r. Sua média condicionada
é E[ZM]/s=r; assim ZM=r quase certamente. Concluímos M_N=rZ.

Retenção do primeiro bit agora importa. Se B1=1, Z só pode ser0 ou1, então
o signed walk só pode terminar em0 ou r. Se B1=0, só pode terminar em0 ou-r.
Logo N>=tau quase certamente no ponto justo. A ruína A34 tem E tau=r para
esse mesmo passeio, independentemente do algoritmo. E N=r e N>=tau implicam
N=tau quase certamente. M_tau determina Z e, com X fixo, também determina Y;
é justamente o último bit da volta/absorção.

Qualquer desvio N!=tau envolve um prefixo finito de bits e um conjunto de
aleatoriedade auxiliar de medida positiva. TODO prefixo binário finito tem
probabilidade estritamente positiva no ponto justo E em qualquer0<p<1.
Assim um desvio positivo em outro p também teria probabilidade positiva no
ponto justo, contradição. Não usar somente continuidade de probabilidades
infinitas; a decomposição em prefixos finitos e a parada a.s. são essenciais.

Para r>=3, depois do primeiro1 é possível alternar níveis1/2 por quantos
passos se quiser, sem atingir0 ou r. Cada tal prefixo tem chance positiva
em todo p interior. Tau portanto tem suporte não limitado; nenhum hard cap
finito pode coincidir com ela quase certamente. QED.

## Oito critérios reavaliados

1. **Uso:** especificar a latência em calls de uma coordenação de dois
   candidatos estruturados cujo primeiro precisa permanecer nativo. O bound
   ajuda decidir o compromisso entre otimalidade esperada e hard cap.
2. **Diferença:** caracterização de igualdade da fronteira output-restrita;
   score, ruína e igualdade em limites de informação são conhecidos. Este
   corolário sozinho não constitui uma segunda grande contribuição/publicação.
3. **Escolha:** quem precisa de hard cap deve usar a aproximação certificada
   ou outra informação, não alegar atingir a mesma fronteira exata com cap.
   Isto é uma garantia de contrato, NÃO vitória de desempenho sobre EPIC.
4. **Prova:** o benefício comparativo é a impossibilidade para TODOS factories
   p-blind retendo B1 no budget uniforme r, e a unicidade do comportamento ótimo;
   não depende de benchmarks, nem presume probabilidade neural equilibrada.
5. **Experimentos:** nenhum novo timing/teste de modelo para o enunciado. Os
   screens negativos continuam negativos; testes de correção não provam
   prioridade, significado acadêmico ou custo útil de uma aplicação.
6. **Custos:** r é número esperado TOTAL de draws, não forwards ou segundos.
   Cauda espectral/cap/custos de consumo precisam do contrato separado A34.
7. **Objeção:** antecedente pode conter a caracterização; retenção restringe
   os comparadores; mais outputs/known-p/ruído ou consumir todos os draws podem
   ser melhores. A cauda inevitável é limitação, não produto científico final.
8. **Artigo:** prioridade e aplicação permanecem abertas. Não apresentar este
   argumento como garantia de aceitação ou investigação encerrada.
