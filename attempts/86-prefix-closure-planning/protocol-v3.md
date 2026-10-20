# A86 — V3: potencial de benefício no replay da trajetória inteira

Congelar este arquivo, `capture_v3.py` e `policies_v3.py` em commit antes de
capturar ou avaliar os dados V3. Os resultados anteriores escolheram contexto
256 e B1/B8; V2 passou em 256 estados reais. Esta etapa **não mede um decoder
acelerado** e não seleciona, sozinha, o tema central.

## Pergunta e fronteira científica

O objetivo executável por prefixos completos escolhe consultas mais úteis que
contagens isoladas, cadeias e variantes com vários pais, depois de cobrar todas
as consultas, a preparação e a distribuição de raízes induzida pela política?
O contrato e as provas estão no README congelado. Closure, Dinkelbach e a
redução de certificados não são contribuições novas. A diferença candidata é
o planejamento de consultas endógenas de canvases dLLM por progresso executável
e custo, cuja relevância prática ainda precisa ser demonstrada.

## Captura e separação dos dados

- Snapshot, NF4/double/BF16, quatro threads, softmax FP32, MASK/EOS/EOT,
  canvas 256, região elegível 128, bloco 32, seleção estável e ausência de KV
  iguais a V2. Seed 86003. Não truncar prompt; exigir `P+128<=256`.
- Os prompts estão literalmente em `capture_v3.py`: quatro TRAIN, quatro
  VALIDATION e oito TEST, metade código e metade explicações em cada split.
  Não substituir, filtrar, reordenar ou acrescentar casos após os dados.
- TRAIN: até 64 eventos por caso. VALIDATION/TEST: até 128 eventos. Parar antes
  se ocorrer EOS/EOT seguro ou preenchimento da região elegível. Um terminal
  seguro pode surgir ao preencher um buraco anterior a um EOS já revelado.
- Capturar apenas o decoder nativo B1, com top-1, confiança e ordem das 32
  posições do bloco por estado, IDs das ações e canvas final reconstruível.
  Não há logits completos novos, treinamento ou downloads.
- Registrar commit, SHA-256 dos produtores/protocolo/planner/perfil/fidelidade,
  versões, carga do modelo separada, custos dos cabeçalhos e custo integral por
  caso, incluindo preparação, terminal, dados e inspeções. Excluir do intervalo
  apenas a escrita do próprio registro de custo. Arquivo novo, nunca sobrescrito.
- Inspecionar processos CUDA antes/depois de cada caso. OOM/interferência:
  preservar parcial e marcar INCONCLUSIVE. Erros, NaN e entrada não suportada
  não são exemplos removíveis. Qualquer caso incompleto impede o gate.

## Estado de uma macro e replay

Começar com o cabeçalho atual em cache; cobrar C(1) uma vez no início da geração.
Congelar tokens top-1 nas primeiras `k=min(8, MASKs no bloco ativo)` posições,
ordenadas pela confiança nativa. Um nó é um subconjunto dessas atribuições,
codificado por máscara de bits; o primeiro evento, bit 0, é conhecido e todos
os conjuntos de consulta o contêm. O universo tem no máximo 128 nós ímpares.

O trace futuro de uma raiz acrescenta ações nativas enquanto posição e ID
coincidem com uma dessas atribuições congeladas. Parar na primeira divergência,
posição fora do pool, terminal ou fim da captura. Não pular estados ausentes
para contar descendentes. Para ajustar tabelas, excluir as últimas oito raízes
de cada TRAIN: o limite de captura não vira evidência de rejeição do draft.

Consultar e cobrar **todos** os nós escolhidos, inclusive os não aproveitados.
O replay avança apenas enquanto todos os estados sucessivos têm seus
cabeçalhos consultados. Parar no último desses cabeçalhos. Na próxima entrada,
o evento final nativo, se terminar por EOS seguro, limite de eventos ou região
completa, pode ser aplicado diretamente do cache sem nova consulta. Não existe
um token bônus não consultado em cada macro. O serial executa exatamente L
forwards para L eventos, inclusive quando L=1.

Uma consulta que completa o bloco armazena o cabeçalho do próximo bloco ativo.
O pool da raiz não inclui novas atribuições desse próximo bloco. Consultas
selecionadas a canvases terminais continuam cobradas; na implementação futura,
projetar o bloco da raiz se não existir novo bloco ativo, sem usar esse
cabeçalho para revelar eventos. Essa convenção é comum a todos os métodos.
O replay não mede essas consultas neurais: usa a tabela de custo declarada.

## Custo fixo e planejadores

Usar exclusivamente as medianas V1 de contexto 256 e B1/B8, arredondadas ao
nanosegundo inteiro pelo `round` de Python. Esses dois tamanhos passaram V2;
não presumir fidelidade B2/B4. Para m consultas, executar ondas B8 e escolher
entre remanescente em B1 ou mais uma onda B8 preenchida:

`C(m)=floor(m/8)*c8 + min((m mod 8)*c1,c8)`, com `C(0)=0`.

Para o planejador de razão, fixar `b=floor((c8-c1)/7)` e
`a=min(C(m)-b*m: 1<=m<=128)`. Exigir a>0 e b>0 e certificar sobre toda a
tabela `L(m)=a+b*m<=C(m)<=kappa*L(m)` com racionais. Essa relação numérica
não é garantia de tempo físico futuro. Os tempos V1 excluem parte do overhead;
por isso este gate identifica somente potencial para uma medição integral.

Construir tabelas por k; frequências inteiras dos prefixos TRAIN alimentam o
planner exato existente. Duas variantes candidatas: global e contextual.
O contexto é o número de posições do pool com confiança >=0,95, em classes
0–1, 2–3 e 4–8. Sem dados da classe, usar a tabela global para k; sem dados
para k, usar serial `{1}`. Nenhum ajuste das classes depois dos dados.

## Controles competentes e seleção prospectiva

Todos compartilham pool, cabeçalho em cache, verificador, custos e paradas.
Escolher configurações por **custo da trajetória inteira em VALIDATION**,
visitando as raízes induzidas por cada política. Congelar as escolhas antes
de acessar as métricas TEST. Não otimizar pela média uniforme das raízes.

1. Serial com reutilização do cabeçalho final.
2. SSD-chain e SSD-mix com N=1,...,8, limitado por k. Mix usa a cadeia e os
   ramos `{1,...,d} union {d+2}`, omitindo a consulta que não contém o primeiro
   evento já conhecido. Verificador comum pode reencontrar a cadeia: é um
   controle fortalecido, identificado como adaptação de SSD.
3. Spiffy adaptado ao mesmo pool e backend: J0 é soma das contagens de nós;
   J1 acrescenta, por nó selecionado, as contagens de seus pais selecionados.
   Seleção conectada por **algum** pai, raiz obrigatória e cardinalidade fixa
   D em 1,2,3,4,6,8,10,12, limitada aos nós observados disponíveis.
   Resolver exatamente por MILP, incluindo produtos binários em J1. Não usar
   a heurística de um único pai do código SpecFold como se fosse Spiffy.
   Não reproduzimos todo o sistema Spiffy nem reivindicamos seus timings.
4. Para SSD e Spiffy, permitir tabelas globais ou contextuais e a escolha de
   N/D separadamente em cada uma das três classes (até 8^3 vetores), usando
   somente VALIDATION. Essa fortificação evita atribuir a vitória ao binning.
5. Spiffy-J0-GM e Spiffy-J1-GM: partir dos grafos ajustados com D=12 (limitado
   pelo pool observado), podando online para D*=1,2,3,4,6,8,10,12, também
   ajustável por classe na validação. Para um nó S, `ell(S)` é a média
   geométrica das confianças da raiz nas suas atribuições; `child(S)` é a
   média geométrica de ell nos filhos do grafo. Folhas usam `child(S)=ell(S)`.
   O score é `sqrt(ell(S)*child(S))`. Manter `{1}` e os D*-1 outros nós com
   maior score, desempate pela máscara inteira, sem reparação posterior de
   conectividade. Essa convenção de folha é nossa adaptação explícita;
   o prefixo efetivamente acessível continua sendo o que conta no replay.

Medir e cobrar a seleção online CPU de todas as políticas por macro, além
de C(m), distinguindo essas duas parcelas nos registros.

O solver MILP usa SciPy/HiGHS, gap relativo zero, limite 30 s por modelo;
preservar status, tempo e gap. Timeout/recusa não vira ótimo nem vitória do
método. Sem os controles exigidos resolvidos, resultado INCONCLUSIVE.
O pool comum só top-1 e as convenções explícitas da poda limitam a comparação:
não afirmar superioridade sobre o sistema Spiffy completo. O artigo não
especifica todas as convenções necessárias para transplantar a poda.

O modo `--audit` confere, sem GPU, a identidade entre prefixos e avanço,
fronteira de bloco, final direto e otimalidade de instâncias pequenas por
enumeração/zeta. Oráculos de correção não são resultados de benefício.

## Critério prospectivo e custo integral

Selecionar uma variante flow e uma configuração de cada família controle na
VALIDATION. Em TEST, exigir em **cada** família de quatro casos que a soma do
custo previsto flow, acrescida de preparação amortizada, seja <=90% do
**mínimo entre os custos dos controles já congelados na validação**, inclusive
serial. Esse envelope oracle de avaliação é conservador para a candidata;
não se reajustam configurações ou se escolhe a variante flow olhando TEST.

Horizonte fixo: 1.000 respostas. A preparação flow inclui captura integral
TRAIN+VALIDATION e todo ajuste/seleção CPU das duas variantes. Registrar carga
do modelo, memória, consultas usadas/desperdiçadas, macros, tempo CPU, ajuste
e validação de **todos** os métodos, sem esconder a busca dos controles.
No gate, dispensar os controles de seus custos de preparação é conservador
para a candidata. Reportar também os custos de preparação reais e o ponto
de amortização quando existir; não declarar ganho para uso único.

PASS autoriza implementar o decoder acelerado e congelar outra avaliação
de latência integral/fidelidade em casos não usados para escolher políticas.
Essa avaliação deverá dispensar consultas a terminais reconhecíveis do canvas
em todos os métodos e incluir o oráculo zeta como controle de benefício quando
o universo observado tiver até 20 nós, além da auditoria de correção atual.
FAIL encerra esta aplicação V3; não mudar margem, casos, bins, custos ou
comparadores para salvá-la. Mesmo PASS não comprova prioridade científica,
qualidade semântica superior, ganho físico ou suficiência para o mestrado.
