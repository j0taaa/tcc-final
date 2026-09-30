# Consulta geográfica com dLLM

A demonstração gera `get_location(name=...)` com LLaDA-8B-Instruct e o mesmo
seletor de produção usado no experimento. Os candidatos vêm do pedido, sem uma
lista de cidades certas. O despachante verifica a AST, o esquema e o suporte;
nunca executa código Python gerado. A única operação externa é GET no endpoint
público de geocodificação do Open-Meteo, com até três localidades.

## Uso

Reprodução de uma execução registrada, sem GPU nem rede:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/run_query_demo.py --mode replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/verify_query_demo.py
```

Inferência nova, com o ambiente CUDA e o snapshot local descritos em
`REPRODUCING.md`, a partir do código testado e commitado:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python scripts/exact_commit/run_query_demo.py \
  --mode live --request 'Find the geographic coordinates of "Belo Horizonte".'
```

`--method` seleciona uma política de `configs/demo/geocoding_v1.json`, incluindo
MWPC, guloso, EPIC e MAP canônico. O padrão é MWPC com confiança 0,8. `--output`
permite escolher uma pasta nova; o comando não sobrescreve registros existentes.
A saída mostra a chamada gerada, localidades, fonte e data de obtenção.

## Limites e evidência

`replay` lê e verifica checksums do registro e da resposta arquivada; não chama
uma execução antiga de inferência nova. `live` registra modelo/revisão, semente,
configuração, commit, suporte, trajetórias e resultado da consulta. Erros de
rede, consulta vazia e geração incompleta têm estados distintos. O serviço pode
mudar depois da data registrada. Texto de entrada deve ser público: o nome
selecionado é enviado ao serviço de geocodificação.

O segundo comando confere também cada testemunha e atualização arquivada:
bytes, suporte, slots físicos, posições já fixadas, propostas selecionadas e
valor objetivo. Essa conferência de viabilidade não substitui os testes do
algoritmo contra os oráculos de otimalidade.

Validade estrutural não prova que a cidade escolhida corresponde à intenção.
A demonstração é um fluxo de uso, não uma estimativa de acurácia ou superioridade.
Há um só campo livre e suporte finito; a API não depende de dLLM para funcionar.
A contribuição do projeto está no controle certificado da geração paralela.

[Documentação da API](https://open-meteo.com/en/docs/geocoding-api).
Dados de localidades: [GeoNames](https://www.geonames.org/).
