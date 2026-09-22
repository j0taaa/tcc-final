# Correções da revisão de 22 de setembro de 2026

Escopo autorizado: resolver os achados da revisão, exceto a discussão de LAVE.
O relatório original foi preservado. A contribuição continua sendo a formulação
MWPC e sua implementação exata por etapa sobre suporte finito.

## Código e contratos

- O parser Rust agora verifica o prazo durante spans vazios e antes de retornar
  uma conclusão de inviabilidade. Duas regressões determinísticas cobrem os
  caminhos que escapavam da contagem de trabalho. A reprodução da revisão
  passou a retornar TIMEOUT nos quatro casos, perto do prazo de 1 ms.
- O driver exato recebe o calendário real de transferência das baselines:
  32 posições, 16 passos e duas propostas por passo no estudo novo. Um teste
  executa o hook e compara os orçamentos observados com a função upstream.
- As baselines e seus testes permanecem intactos. O problema de tensores do
  primeiro piloto foi corrigido no observador externo, com teste de regressão;
  as 18 falhas originais continuam arquivadas.
- O histórico de correções M14--M16, incluindo acumulação exata de pesos
  binary64 e validação de certificados, foi preservado em commits locais.

## Evidência nova

Os dados, configurações, certificados, falhas e hashes estão em
docs/artifacts/raw/m17_review_v1. A análise é regenerada por
scripts/exact_commit/build_review_results.py; a saída estruturada está em
paper/generated/m17_review_v1/summary.json.

| Estudo | Resultado observado |
| --- | --- |
| Configurações sintéticas recursivas | 1.200; zero divergências entre Python, Rust e enumeração; 828 com mais de uma conclusão válida; perda da heurística em 12 condições. |
| Replay de logits reais | 24 estados pré-fixação, sem inserir resposta; K=2,4,8; 72 pares, 60 viáveis e 12 inviáveis; empate nas 60 condições viáveis. |
| Escala recursiva | 72 execuções; 66 ótimos e seis timeouts; até 1.282 nós e 2.048 arestas; máximo observado de RSS de aproximadamente 77 MiB. |
| Piloto corrigido | 12 tarefas; 48 gerações comparadas e 12 capturas; exato concluiu 1/12 e teve zero sucessos funcionais; serial/EPIC concluíram 7/12 e tiveram 3/12 sucessos. |
| Confirmação disjunta | 12 tarefas novas, duas repetições; 96 gerações e 12 capturas; exato concluiu os oito ensaios de colchetes, mas nenhum cumpriu as exigências funcionais; aritmética/JSON ficaram incompletos. Serial/EPIC tiveram sucesso em uma tarefa JSON, repetida duas vezes. |

Repetições e condições de suporte não foram apresentadas como novas tarefas
independentes. O estudo sintético é condicionado à existência de uma resposta;
o replay real não é. O piloto com erro operacional permanece separado da
comparação. A confirmação não alterou tarefas, orçamento ou critérios para
obter um resultado positivo.

O replay v1 herdava o seed da configuração de escala, embora não sorteasse\nnovas entradas. Foi preservado como replay-v1; o replay principal foi repetido\ncom o seed correto da captura e proveniência por tarefa/passo.\n\nEsses resultados resolvem as lacunas de medição, mas não demonstram vantagem
prática geral. O artigo agora explicita essa conclusão. Os antigos fatores
de tempo 0,524 e 0,625 são identificados como confundidos por orçamentos
diferentes; as medições históricas não foram reescritas.

## Artigo

O Algoritmo 2 recebe CNF estrita, normaliza epsilon com proveniência, compara
o melhor caminho inteiramente epsilon e processa spans topológicos. A
restrição H foi colocada no nível de tokens, antes da detokenização.
A proposição de término explicita que não vale para um orçamento menor que
interrompe a execução. O exemplo desenvolvido mostra uma escolha gulosa de
peso 4 perdendo para duas propostas compatíveis de peso total 5.

Abstract e resumo descrevem resultados concluídos; o português usa fixação
de tokens e sequência completa válida. Detalhes extensos de hardware e
correspondência com arquivos foram movidos ao suplemento. As tabelas novas
incluem falhas, conclusão, sintaxe e sucesso funcional. Testes documentais
acompanham os arquivos do suplemento; eles não substituem os novos testes de
comportamento. A declaração de IA distingue a assistência da revisão final
que cabe ao autor.

## Verificações

- Suíte Python: 837 testes passaram.
- Rust: 21 testes unitários e três diferenciais passaram; format/Clippy
  passaram nas duas crates.
- M5, M6 e M7: 500/500 casos por campanha, sem divergência.
- Baseline upstream: 19 testes passaram; quatro skips já declarados.
- Ruff e MyPy: passaram; 78 arquivos Python verificados por MyPy.
- Artefatos históricos e novos: hashes e reconstrução determinística passaram.
- Wheel/sdist 0.2.0: instalação isolada, imports, experimento e geração de
  artefato passaram, sem importação acidental da árvore de desenvolvimento.
- PDF: compilado e inspecionado visualmente; ajustes de espaçamento corrigiram
  definições encostadas e os resumos cabem na primeira página.

Comandos principais: python -m pytest -q; make test-rust-parser;
os três runners M5/M6/M7 com --campaign normal; os dois arquivos de testes
upstream indicados em AGENTS.md; ruff check src tests scripts; mypy src;
make final-artifacts-check article-results-check; scripts/rehearse_release_wheel.py;
make -C paper. Os executáveis Python foram os ambientes locais fixados do projeto.

Os gates de checkout limpo e os arquivos finais da release são registrados
abaixo depois de concluídos. A entrega v0.2.0 é local; não houve push remoto.
