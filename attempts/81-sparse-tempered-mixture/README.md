# A81 — Potência fracionária de uma mistura gramatical

Versão teórica V1, anterior a qualquer implementação ou campanha desta tentativa.
A [prova escrita](theory.md) passou por revisão independente de um subagente
(R31-B, 20/10/2026). Isso não é revisão humana, verificação Lean, demonstração
de prioridade mundial ou medição de desempenho. A contribuição própria útil
e a meta de três temas continuam abertas.

## Operação e benefício demonstrado

Sobre um domínio finito de palavras de IDs originais, queremos amostrar

$$
Q_\beta(x)\ \propto\ 1_G(x)[t_1(x)+t_2(x)]^\beta,
\qquad \beta\in\mathbb Q,\quad\beta\ge1.
$$

Cada peso é um produto de fatores locais sobre a mesma derivação única.
Isso inclui dois produtos posicionais condicionados pela mesma gramática,
ou dois priors gramaticais ponderados combinados com um head congelado.
Os fatores e a definição do alvo são públicos nesta operação; não se exige
treino para especificar os priors.

O compilador prepara no máximo

$$
R=\lceil2\sqrt\beta\rceil+1
$$

gramáticas ponderadas sobre o mesmo plano. Uma correção por rejeição produz
exatamente o alvo, com menos de 19 propostas em esperança antes do
arredondamento certificado. A realização racional tem limite menor que
19 vezes o fator declarado de majoração. A aceitação avalia somente a
âncora proposta, os dois pesos originais e uma região racional.

O ganho teórico é contra a expansão por réplicas: para dois componentes e
grau inteiro próximo de beta, ela prepara ordem beta de charts; aqui são
ordem raiz de beta. Para envelopes monomiais positivos universais com
fator constante permitido pelo teorema, essa ordem é ótima. O inferior
não cobre todos os amostradores nem métodos adaptados a uma entrada.

Esse ganho de representação não demonstra ganho total de tempo, economia
de forwards, qualidade semântica ou enquadramento integral em 12 GB.
Para beta pequeno, réplicas ou outros envelopes podem ser mais baratos.

## Hipóteses e limites

- O domínio é finito, com slots e pins declarados, massa alvo positiva e
  um plano acíclico não ambíguo. Os dois componentes usam a mesma estrutura
  e o mesmo testemunho de cada palavra. Um limite D para a quantidade de
  fatores por testemunho integra a preparação.
- IDs aliases são eventos distintos. Preservam-se IDs, multiplicidades,
  bytes e posições fixadas. EOS e PAD estão ausentes nesta versão. Suporte
  podado recebe somente exact_on_support, com cauda omitida separada.
- Pesos de entrada são racionais não negativos. Zeros são preservados.
  Componentes já condicionados e normalizados exigem incorporar e pagar
  seus normalizadores; omiti-los define outra mistura.
- A garantia é da potência da mistura marginal inteira. Sortear um
  componente e temperá-lo, ou temperar condicionais sequenciais, geralmente
  define outra lei. O alvo não é a trajetória nativa de uma dLLM.
- A realização usa propostas e RNG novos. O teorema pressupõe bits
  uniformes independentes; seeds de PRNG não provam esse pressuposto.
  Massa zero, entrada não suportada, erro e recusa por recursos são distintos.
- A extensão não cobre automaticamente PCs profundos não determinísticos,
  gramáticas ambíguas, interseção de planos incompatíveis ou mudança de
  semântica. Não há alegação de que todo JSON esteja contemplado.

## Antecedentes e diferença candidata

O instrumento de discretização de Bernoulli em coordenadas angulares tem
antecedente direto em
[de Rooij–van Erven, AISTATS 2009, §3.1](https://proceedings.mlr.press/v5/rooij09a/rooij09a.pdf).
O grid de Fisher não é uma invenção desta tentativa.
[Hsiung–Kim–Boyd, 2008, §3.2](https://web.stanford.edu/~boyd/papers/pdf/rgp.pdf)
aproximam log-sum-exp por máximos de tangentes; isso se relaciona a máximos
de monômios inferiores. Um máximo não fornece diretamente a massa
gramatical de uma soma positiva. A prova controla a sobreposição das
parcelas para evitar pagar um fator R ao trocar máximo por soma.

[Coreᵏ, IJCAI 2017, Algoritmo 1 e Lema 1](https://www.ijcai.org/proceedings/2017/0334.pdf)
já amostra potências inteiras de tensores CP não negativos.
O [Atlas, Teoremas B.6–B.7](https://arxiv.org/html/2102.06137v1) estabelece
operações de potência sob seus contratos de determinismo e compatibilidade.
Rejeição com envelopes pertence ao contexto clássico de
[OS*, §2](https://arxiv.org/html/1207.0742v1).

A contribuição candidata é o pacote: soma positiva universal com ordem
ótima de parcelas nesta classe, compilação sobre o plano gramatical e
correção conjunta com partição racional. A busca e a revisão R31-B não
identificaram esse pacote completo nas fontes examinadas; sua prioridade
suficiente continua pendente.

## Consumidor, comparadores e custo completo

O consumidor proposto é um sampler de geração ou infilling estruturado com
dois priors ponderados, derivação comum e head congelado. O temperamento
conjunto é uma operação relevante em decoders com misturas:
[CoDD v3, §5.1](https://arxiv.org/html/2603.00045v3) descreve essa dificuldade
e aproximações. A aplicação treinada e os PCs gerais desse artigo excedem
nosso contrato. Ainda não foi escolhido um caso dLLM com vitória integral.

Antes de medir, os controles precisam incluir:

- expansão inteira e fracionária por réplicas, escolhendo o grau por custo;
- envelopes normativos otimizados, secante de um chart quando a razão
  dos priors tem amplitude pequena e refinamentos OS*;
- histogramas quando há poucas razões distintas, decomposição por regiões
  simples e enumeração quando o suporte permite;
- aproximações com TV certificada e MAP quando sua concentração é certificável.

Para um plano de tamanho S, M saídas realmente solicitadas e mensagens de
até B bits, a contabilidade precisa incluir

$$
T_{\rm comum}
+R(T_{\rm fatores}+T_{\rm inside})
+M\,19\eta(T_{\rm sorteio}+T_{\rm avaliação}
+T_{\rm região}+T_{\rm moeda})
+T_{\rm saída/validação}.
$$

T comum inclui compilação lexical/gramatical, backbone, head denso, leitura
e transferências, além do head elevado compartilhado quando aplicável.
Preparação de fatores, aritmética multiprecisão, normalizadores, seletores,
RNG, reconstrução e emissão são pagos. A memória dos charts é O(RSB) bits;
fatores lexicais particulares podem exigir memória adicional ou recomputação.
RAM da CPU e VRAM são contabilizadas separadamente. A prova não precisa
de outside.

O crescimento de B pode depender do valor de beta. Contar raiz de beta
de charts não prova tempo polinomial no comprimento binário de beta.
Não existe amortização gratuita entre heads distintos ou saídas não pedidas.

## Evidência preservada e pendências

Esta versão preserva a prova e a especificação. Os oráculos finitos relatados
na [revisão R31-B](t3-thread://v1/thread:delegated-task:command%3Amcp%3A0500190c-aab1-49b6-b9b0-4a249c29550e%3Adelegate-task%3Abetter-ideas-20261020-r31-sparse-power-compiler)
complementaram a análise; seus scripts inline não constituem um executável
versionado de reprodução desta tentativa. Não há resultado de campanha,
teste de um amostrador implementado ou medição neural A81.

Faltam a auditoria específica de prioridade e um consumidor que sobreviva
aos controles fortes com custo completo. Nenhum protocolo de medição está
selecionado. Uma campanha futura precisa de protocolo congelado e commit
produtor próprios, anteriores aos dados.

Este commit congela a versão teórica V1. Correções científicas posteriores
ficam separadas, com origem e erro explícitos; não se sobrescreve a fonte
para melhorar um resultado.
