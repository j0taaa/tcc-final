# Limite de rejeições contra a atualização publicada do CARS — M36

Direção atual de pesquisa: vantagem provada na contagem sob hipóteses explícitas; não é latência universal, prioridade confirmada ou revisão humana.

Esta pasta preserva a abordagem, incluindo resultados desfavoráveis, sem
promovê-la a contribuição inédita ou a decoder de produção.

- [Código, provas, dependências e artigo congelados](v1/source.zip).
- [Entradas, saídas e resultados arquivados](v1/evidence.zip).
- [Proveniência e inventário SHA-256 por arquivo](v1/manifest.json).
- Código original: `2af7b8f572bca8b1d61d397a275707c2ce8bd343`.
- Versão dos arquivos de evidência: `2af7b8f572bca8b1d61d397a275707c2ce8bd343`. Os commits produtores
  de cada medição continuam nos metadados originais; este hash é de preservação.
- Leitura principal dentro do snapshot: docs/evidence/m36-adaptive-semantics.md; paper/semantic-conditioning.tex; tests/test_adaptive_semantics.py.

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
