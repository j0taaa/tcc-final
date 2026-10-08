# MWPC original e validação inicial

Base preservada: ótimo de um passo no suporte declarado; não implica vantagem geral de geração.

Esta pasta preserva a abordagem, incluindo resultados desfavoráveis, sem
promovê-la a contribuição inédita ou a decoder de produção.

Além da versão consolidada, as etapas mais antigas estão preservadas literalmente:

- [Estado inicial do repositório](initial-repository/source.zip), commit
  `836540d18fd0c37ae9f0d577e5c25ca508dfd13b`: apenas o README inicial, sem solver.
- [Primeiro protótipo completo do MWPC](first-working-prototype/source.zip),
  commit `6a5945bef2e9c6dc55ad8d0d02f91656215ac6aa`: etapa M2, parser max-plus
  alinhado a tokens, normalização e reconstrução/validação do testemunho.
- [Versão consolidada da primeira abordagem](v1/source.zip), etapa M17.

Cada etapa tem seu próprio `manifest.json` e hashes. As evidências do protótipo
ficam no código/documentação históricos; os ZIPs separados de evidência dessas
duas etapas são vazios. Não foram inventados resultados antigos nem executada
a suíte histórica. A versão `v1/` publicada anteriormente permanece intacta.

- [Código, provas, dependências e artigo congelados](v1/source.zip).
- [Entradas, saídas e resultados arquivados](v1/evidence.zip).
- [Proveniência e inventário SHA-256 por arquivo](v1/manifest.json).
- Código original: `a309b1c847bd7396db60aadcca255be93ff7d140`.
- Versão dos arquivos de evidência: `2af7b8f572bca8b1d61d397a275707c2ce8bd343`. Os commits produtores
  de cada medição continuam nos metadados originais; este hash é de preservação.
- Leitura principal dentro do snapshot: TASKS.md; paper/main.tex; docs/evidence/m17-review-verification.json.

O ZIP de código contém a árvore do projeto naquela versão, exceto arquivos
brutos/processados (incluídos separadamente para esta tentativa), pastas de
arquivamento e eventuais submódulos externos. Os submódulos são identificados
pelo commit no manifesto. Versões antigas podem incluir testes históricos
**dentro do ZIP**; eles não foram restaurados na suíte ativa.

Nenhum arquivo é um link para o código atual. Os ZIPs não incluem pesos de
modelos, caches ou logits completos locais. Dependências e ferramentas precisam
ser instaladas conforme as instruções congeladas; preservar os bytes não torna
uma reprodução histórica automaticamente executável sem essas dependências.

A leitura dos ZIPs e a verificação de integridade são offline. Veja
[as instruções de acesso](../README.md). Não edite `v1/`; uma continuação deve
usar `work/` e uma nova versão congelada (`v2/`, etc.).
