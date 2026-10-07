# M34: contribuição implementada e seu alcance

O projeto agora oferece um componente de inferência para dLLMs que calcula a
massa gramaticalmente válida, as probabilidades marginais dos tokens e amostras
exatas da predição fatorizada condicionada a uma gramática recursiva LL(1)
verificada. Preserva tokens originais, aliases, subpalavras, posições fixas e
massa descartada; reutiliza a floresta quando mudam pesos ou são fixadas posições.
O núcleo novo tem 554 linhas de Python, sem dependências de modelos. A suíte
antiga continua removida; há oito testes novos, específicos e independentes.

A utilidade matemática é explícita. Documentos JSON construídos com escolhas
entre arrays e objetos aninhados exigem 2^d configurações numa representação
sequencial explícita. Na mesma família, rejeição independente exige 2^d tentativas
em média sob probabilidades uniformes. A gramática é fixa e a inferência na
floresta usa trabalho polinomial, inclusive em bits após a normalização. Isso
não precisa de um benchmark favorável. São princípios estabelecidos adaptados
ao contrato de tokens finitos, não descobertas exclusivas deste trabalho.

EPIC e LAVE não calculam essa distribuição conjunta exata. Métodos clássicos de
CFG e algumas codificações de fatores podem oferecer a mesma capacidade; não
há alegação de ser o primeiro algoritmo de amostragem gramatical ou de vencer
qualquer implementação. A pesquisa de fontes primárias identifica o espaço
incremental de integração, não comprova prioridade científica mundial.

A auditoria retém todos os 28 casos de escala, 18 predições antigas do MDLM e
nove novas. Os 52 resultados inicialmente resolvidos mantêm massas e marginais
idênticas após refinamento; passam oito de nove JSONs novos, com uma recusa por
orçamento. Contadores de arrays geralmente custam menos. Rejeição é mais barata
nos seis JSONs menores no seed registrado; esgota 10 mil tentativas em 13 dos
27 casos, sem provar inviabilidade. Reutilização coincide com recompilação nos
26 casos resolvidos. Não se mede superioridade semântica, da trajetória neural
completa ou de um decodificador publicado. Resultados completos e tempos:
`docs/artifacts/processed/m34_cfg_posterior_v1/report.md`.

Verificações executadas:

- `make check`: snapshot EPIC, Ruff e MyPy (57 módulos) passam.
- `make test`: oito testes passam; produtos de tokens com reconhecedores
  independentes, lei de amostragem por transcritos de RNG, restrição/reuso,
  família JSON e 281 casos externos definidos + 33 informativos.
- `make build-rust`: fontes retidas e bindings passam formato/Clippy.
- `make check-formal LAKE=/home/jota/.elan/bin/lake`: 41 declarações auditadas,
  biblioteca e exemplo canônico passam. A prova completa do sampler, tokenizer
  e código Python/Rust não está mecanizada; seu alcance permanece explícito.
- `make article-results-check`: 3.683 arquivos antigos preservados, auditoria M31
  e arquivos/produtos M34 passam. Florestas/probabilidades originais são
  reconstruíveis de arquivo compacto sem rede. Fonte/config/comando/commit e
  todos os resultados, inclusive falhas iniciais, estão registrados.
- `check_cfg_model_capture --capture results/raw/m34_cfg_posterior_v1/json-model`:
  nove logits completos locais passam hash, softmax sem MASK, normalização
  racional integral e seleção original top-32.
- `build_probability_audit_results --check --capture results/raw/m31_probability_v1/capture`:
  os 18 logits completos antigos também passam sua verificação independente.
- `make paper`: 16 páginas, sem overflow/referências indefinidas. Revisão visual
  do conjunto e páginas do método/tabela feita sobre o PDF final.

O artigo centra a nova capacidade e conserva resultados negativos. Provas
anteriores mais extensas continuam nos suplementos/fontes, sem alterar seus
hashes. O arquivo científico novo ocupa aproximadamente 1,6 MB; componentes
repetidos são deduplicados sem perda. Logits, pesos e imagens de revisão
permanecem locais. Testes e demonstrações não são uma prova universal de fonte.
