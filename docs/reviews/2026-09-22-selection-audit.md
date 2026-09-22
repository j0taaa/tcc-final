# Auditoria da alegação de vantagem prática

A conclusão anterior era forte demais. Há um ganho computacional reproduzível
do seletor exato para os lotes maiores deste conjunto, mas sua magnitude depende
do comparador. Isso não demonstra melhor geração completa nem melhor resposta
ao usuário.

## Comparador, cronômetro e novo controle

O guloso anterior reconstruía o problema mesmo quando a testemunha já provava
a aceitação de uma proposta. A opção `reuse_witness=True` elimina essas consultas:
se a testemunha válida já coincide com a proposta, ela também satisfaz a nova
fixação. As consultas seguintes recebem todas as fixações acumuladas. Não há
poda de caminhos ou alteração da política gulosa. O comportamento padrão foi
preservado, e as duas variantes aceitaram exatamente as mesmas propostas nos
540 pares viáveis; os outros 108 pares concordaram na inviabilidade.

Também havia uma assimetria no limite: o exato recebia um segundo para o parser,
e o guloso um segundo para a seleção inteira. Nenhuma chamada exata antiga
ultrapassou um segundo de tempo total (máximo observado: 0,752 s), portanto
isso não invalida suas classificações observadas. Contudo, a comparação nova
aplica a mesma verificação de prazo total aos três métodos, incluindo os
validadores. Resultados tardios são TIMEOUT, sem pontuação nem certificado.

O protocolo foi congelado no commit
`196d48c`, antes da medição:
[`m19_selection_audit_v1.toml`](../../configs/experiments/m19_selection_audit_v1.toml).
Ele reutiliza todos os 24 estados dos 12 prompts de confirmação, K=2/4/8 e
orçamentos de até 2/8/32 propostas. São três repetições em processos novos,
com rotação da ordem dos três métodos e limite total de dez segundos.
O prazo maior permite observar todos os pares sem descartar os casos lentos.
As propostas, seus pesos e o suporte são idênticos entre os métodos. Verifiquei
também que o orçamento 2 reproduz as propostas originais em todos os 24 estados.

## O que os dados permitem afirmar

Todas as 1.944 execuções terminaram. Cada método teve 540 resultados viáveis e
108 inviabilidades no suporte, sem timeout ou erro. Para o exato, os resultados
viáveis são ótimos certificados. Contra o guloso com reaproveitamento, as medianas
das razões tempo-guloso/tempo-exato, variando K, foram:

- Até 2 propostas: **0,96–1,00**; nenhum ganho claro para o exato. Ele foi mais
  lento em 34 das 60 combinações viáveis de estado e largura.
- Até 8 propostas: **1,71–2,05**; o exato foi mais rápido em 16 dos 20 estados
  viáveis em cada largura, e mais lento nos quatro restantes.
- Até 32 propostas: **2,35–3,82**; o exato foi mais rápido nos 20 estados viáveis
  de cada largura.

Primeiro se calcula a mediana das razões das repetições em cada estado; depois,
a mediana entre estados. Não é uma razão das medianas globais dos tempos.
O [resumo gerado](../../paper/generated/m19_selection_audit_v1/summary.json)
inclui também os tempos absolutos, as perdas e o controle sem reaproveitamento.
No novo controle, esse comparador original dá razões de 9,13–15,71 para orçamento
32, mostrando quanto da aparente vantagem vinha das consultas redundantes.

No caso com diferença de pontuação, as medianas foram 48,4 ms para exato,
641,6 ms para guloso original e 113,3 ms para guloso com reaproveitamento.
O número de consultas de viabilidade caiu de 33 para 10. Essa é uma economia
do componente, não uma aceleração medida da geração completa.

## O caso “31 contra 30”

A diferença de pontuação é correta, confirmada em Python e Rust. Entretanto,
os totais incluem os mesmos **23 EOS/PAD** em ambos os métodos: são **8 contra
7 propostas de conteúdo**. A condição é
`confirm-brackets-3-170302-capture-forward0`, K=4, orçamento 32.

O prompt pede quatro pares redondos, três quadrados e profundidade mínima três.
A testemunha exata é `()()()()()()()()()` — nove pares redondos, nenhum quadrado,
profundidade um. A gulosa é `[[()()()()()]()]` — seis pares redondos, dois
quadrados, profundidade três. **Ambas falham no pedido.** O objetivo sobe de
14,203307921409227 para 14,318663361719748, mas maior soma de probabilidades não
equivale a melhor resposta ao prompt.

Nenhuma das 540 testemunhas viáveis de cada método passou no verificador
funcional. São completamentos certificados de estados salvos, não novas
gerações completas do modelo. Os resultados ao vivo continuam sem demonstrar
vantagem de qualidade, conclusão ou tempo total.

## Alcance e reprodução

Os tempos excluem inferência, extração top-K e preparação do suporte comum.
Os estados usam IDs locais compactos. Mesmo com reaproveitamento, o guloso
ainda reconstrói o lattice e usa o parser ponderado para consultar viabilidade;
não é um parser booleano incremental nem a implementação EPIC. Há apenas
12 prompts, três gramáticas pequenas, um checkpoint e uma máquina; repetições,
larguras e estados do mesmo prompt não são novas amostras independentes.

A afirmação defensável é: **neste benchmark, o seletor exato reduz o custo de
selecionar lotes maiores frente ao guloso avaliado, com garantia de ótimo no
suporte; uma vantagem prática do sistema completo permanece não demonstrada.**
O resumo, os resultados, as limitações e a conclusão do artigo foram corrigidos.
O estudo anterior e seus dados foram preservados como evidência histórica.

Dados brutos, certificados, hashes dos estados, configuração e metadados:
[`m19_selection_audit_v1`](../artifacts/raw/m19_selection_audit_v1/).
Os comandos de medição e regeneração estão em [REPRODUCING.md](../../REPRODUCING.md).
Validação: 842 testes Python; 24 testes Rust, formatação e Clippy; Ruff e MyPy
sem erros. Os testes novos cobrem equivalência da seleção em 40 seeds por
backend e rejeição de um resultado exato que termina depois do prazo total.
Os hashes dos arquivos brutos, dos 24 estados e da configuração no commit
produtor foram conferidos; os valores antigos e novos foram regenerados sem
divergências. O PDF corrigido tem 18 páginas, sem caixas excedendo as margens
ou referências indefinidas; as páginas alteradas e vizinhas foram inspecionadas.
Arquivo local: `dist/mwpc-exact-selection-audit-paper.pdf`.
