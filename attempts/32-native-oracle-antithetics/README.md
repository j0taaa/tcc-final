# A32 — Acoplamento nativo por classes com orçamento de oráculo

Iniciada2026-10-11. Candidata, NÃO novidade/publicação confirmada. Independente
de31/v3; seu piloto negativo não é convertido em evidência desta operação.
Antes de implementar, o contrato e as oito perguntas são registrados abaixo.

1. **Uso real.** Dois candidatos JSON/DSL de uma dLLM com EPIC completo e
   verificador/dry-run. Retém literalmente o primeiro candidato e altera
   dependência entre candidatos, preservando cada lei nativa inclusive a
   ordem usada na recuperação. Ruídos adicionais do mesmo head são baratos
   relativamente a forwards, mas seu custo entra completo. Pass@1 não muda.
2. **Relevância/diferença.** Bernoulli factories, Barker, Dirichlet, dependent
   rounding e antithetic sampling são conhecidos. Candidata: limiar MÍNIMO
   de quatro draws p-blind para melhoria estrita de cobertura, limite ótimo
   por orçamento e realização adaptativa ótima nesse limite com menos de
   um draw auxiliar esperado. A aplicação trata o sampler nativo finito como
   oráculo e não substitui sua lei por PL ideal. A suficiência deste recorte
   para artigo ainda exige revisão de antecedentes e uso real competitivo.
3. **Escolha.** Sem avaliar a probabilidade verdadeira das classes, mantém
   a lei nativa inteira e a primeira resposta. Para toda propriedade final,
   pass@2>=iid do MESMO decoder e variância média<=iid. Um efeito que distingue
   duas classes equilibradas ganha6.25 pontos percentuais de cobertura local
   (0.75->0.8125), NÃO medição de acerto neural. Comparadores: EPIC iid2/iid4,
   A31/root/history, antitéticos com probabilidades conhecidas, CARMS/CDF,
   repair de colisões por palavra e diversidade completa quando aplicável.
4. **Matemática.** Oráculo iid arbitrário P, projeção binária c e primeiro
   draw inalterado. Segundo draw independente; só em colisão de classe, um
   proposal e um coin adicional tentam trocar para a classe oposta. Provar
   marginais, covariância, custo, limite de Bernstein para n draws, otimalidade
   n=4 e corolário adaptativo Markov/CFG. NÃO lower bound de algoritmos que
   conhecem p, acessam densidades/side information ou mudam a marginal.
5. **Validação honesta.** Enumeração independente de TODOS draws em pequenos
   P/projeções/funções e kernels adaptativos; não benchmarks inventados.
   Primeiro replay nativo com heads falsos e fonte pinada; depois protocolo
   externo congelado, dados/seed/gates definidos antes de heads. Preservar
   todos fracassos. O piloto31 tem casos fáceis e NÃO confirma32.
6. **Custo completo.** Até dois draws auxiliares por encontro, esperado
   1-p(1-p)<=1; inclui classificar e armazenar chave e D2H/H2D. Nenhum forward
   auxiliar para coordenar; mais diversidade pode causar MAIS forwards
   únicos e reduzir caching. Contabilizar isso, preparação e verifier/saída.
   Overhead tem limite determinístico; ele não prova latência total menor.
7. **Objeções.** Saber p permite antitéticos mais fortes; a bound só vale ao
   acesso p-blind declarado. Classificação sem relação com o valor futuro
   dá ganho zero. Sampler4 draws é ruído, não quatro gerações completas, mas
   iid4 é comparador importante na fronteira de custo. Agrupar outras partes
   do estado incorretamente pode perder garantias. Mesmo efeito já conhecido
   ou alternativa exata mais barata pode refutar novidade. Rejeitar direção
   se for só aplicar uma fábrica/Barker sem resultado distintivo útil.
8. **Artigo.** Faltam conferir fontes primárias, provar limite/gain, encontrar
   contraexemplos, implementar referência mínima e testar utilidade externa.
   Nada disso é concluído apenas por criar este README. Não há revisão humana,
   aceitação ou superioridade geral sobre EPIC. Não modificar vendor/31.

## Estado

Contrato: sampler finito nativo de ruído/ordem, não posterior CFG nem MWPC.
Projeção/posição dependem só do estado/head e política comum, nunca de gold.
Massa da classe serve à análise, NÃO é input exigido do algoritmo.
Uma ordem inteira retorna de um draw original; não trocar só o vencedor.
As fontes de31/v3 permanecerão congeladas. Copiar apenas fonte pinada com
hash/atribuição se necessário; não importar sua implementação mutável.

## Gate inicial executado

`work/theory-v1.md` contém a prova escrita e o limite oracle-only. Quatro
oráculos independentes passam0.766s: todas as classes/distribuições pequenas,
eventos/scores, orçamento e729 sequências de kernels adaptativos. O limite
contra métodos que sabem p NÃO é reivindicado. Antecedentes e pendências em
`work/antecedents-v1.md`; novidade do limite específico ainda aberta.

`work/probe_native.py` executou216 casos do EPIC pinado, com heads FALSOS:
216 primeiras trajetórias iguais, inclusive recuperação/EOS/rejeições e
isolamento de RNG CPU/CUDA;156 nós compartilhados,128 draws auxiliares,
978 calls FALSAS. Todos hashes em `work/evidence/native-fake-v1.json`.
O draft que falhou por device CUDA implícito está preservado separadamente.
Nenhum forward neural novo nem timing competitivo para32 até este ponto.
Classe binary cumula CDF do head somente para escolher uma partição antes
do ruído; essa estimativa NÃO é usada como probabilidade verdadeira na troca.
Cada troca devolve o vetor de ruído original inteiro do row, sem cortar cauda.
Suíte offline127 testes passa65.861s; Ruff explícito dos novos fontes passa.
