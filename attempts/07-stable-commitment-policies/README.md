# Políticas de commitment e confirmação externa — M24

Histórica: manter perdas, resultados externos, ablações e análises posteriores separados dos protocolos primários.

Esta pasta preserva a abordagem, incluindo resultados desfavoráveis, sem
promovê-la a contribuição inédita ou a decoder de produção.

- [Código, provas, dependências e artigo congelados](v1/source.zip).
- [Entradas, saídas e resultados arquivados](v1/evidence.zip).
- [Proveniência e inventário SHA-256 por arquivo](v1/manifest.json).
- Código original: `3ecfd44dec63d9afa74e89201e6b807080439d7b`.
- Versão dos arquivos de evidência: `2af7b8f572bca8b1d61d397a275707c2ce8bd343`. Os commits produtores
  de cada medição continuam nos metadados originais; este hash é de preservação.
- Leitura principal dentro do snapshot: docs/research/m24-findings.md; docs/research/m24-reproduction.md.

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
