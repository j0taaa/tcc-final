# O que a aplicação de reparo demonstrou

Fonte de medição: commit limpo `47b93c4`, três configurações M21 congeladas.
Foram 384 chamadas no piloto, 3.840 na confirmação e 768 na ablação de gramática:
4.992 no total. O [relatório gerado](../../paper/generated/m21_repair_v1/report.md)
mostra todas as classes, perfis, falhas, tempos e comparações pareadas. O
[protocolo](m21-repair-protocol.md) registra a hipótese e os controles antes dos resultados.

## Vantagem observada e mecanismo

Na confirmação, os 20 documentos com aberturas de objetos trocadas foram recuperados
integralmente pelo exato em ambas as repetições, em bytes e com o tokenizer real do
LLaDA. O json_repair 0.63.5 recuperou 0/20, inclusive nos modos com esquema standard
e salvage. A diferença diz respeito aos dados recuperados: um JSON válido com
payload vazio não conta como acerto. O mesmo resultado apareceu nas trocas de
fechamentos. Cada documento tem três/quatro registros; valores são novos em relação
ao piloto, mas os mecanismos de corrupção são compartilhados.

Nesse esquema rígido, o parser sem pesos, o guloso e a enumeração também recuperam
os dados. Portanto, esse resultado sozinho demonstra o benefício da restrição
gramatical para a classe testada, não a necessidade da otimização ponderada.

Na ablação com gramática JSON ambígua, o exato recuperou 8/8 aberturas corrompidas;
guloso, parser sem pesos e os três modos da biblioteca recuperaram 0/8. A enumeração
com esquema também acertou 8/8 e foi mais rápida. Este é um caso concreto em que
resolver o objetivo global por etapa, em vez de aceitar propostas em ordem, melhora
o reparo. Não é uma alegação de novidade do conceito geral de parsing ponderado.

Exemplo arquivado, documento 213000, perfil LLaDA:

```text
Entrada: {"id":650,"payload":[["a":87,"b":54}]}
Exato:   {"id":650,"payload":[{"a":87,"b":54}]}  (1 token alterado)
Guloso:  {"id":650,"payload":[["a",87,"b",54]]}  (3 tokens alterados)
```

O guloso conserva a abertura errada e adapta o restante a uma lista. O exato pode
abrir mão dessa proposta e preservar mais tokens globalmente. Ambos recebem a
mesma gramática, suporte, pesos e intervalos protegidos, sem o objeto esperado.

## Custos e resultados contrários

- No perfil LLaDA, a mediana por documento da confirmação de aberturas é cerca de
  387 ms no exato e 547 ms no guloso. As bibliotecas custam cerca de 1 ms ou menos.
  A vantagem de recuperação não é uma vantagem de velocidade sobre bibliotecas.
- Na confirmação de separadores, exato e guloso recuperam 20/20. Enumeração
  recupera 10/20 com LLaDA e 0/20 em bytes; os outros casos esgotam dois segundos.
  O parser sem pesos também acerta todos; não há ganho exclusivo dos pesos aqui.
- Quando falta o delimitador final, a biblioteca recupera 20/20; o suporte fixo
  do exato não representa inserções e recupera 0/20. Inviabilidade e timeout são
  registrados separadamente.
- Com gramática ambígua e separadores trocados, o exato recupera 0/8 e o guloso
  8/8. No exemplo de um registro, há empate de custo entre restaurar o objeto e
  convertê-lo em lista. Minimização exata não resolve uma ambiguidade semântica.
- Nenhum método recupera os valores factuais alterados que já formam JSON válido.
- A solução sem pesos é uma ablação de uma única consulta, sem atalho para entradas
  válidas. Sua alteração de controles válidos não deve ser vendida como uma derrota
  de um pipeline de produção com validação prévia.

## Contribuição defendível

O trabalho entrega uma aplicação executável do MWPC a reparo de substituições,
com custo mínimo no suporte, preservação de trechos por token, certificado e
validação independente. O experimento identifica um domínio restrito em que ela
preserva informações que uma biblioteca prática perde; a ablação explica quando
os pesos fazem diferença. O artefato reproduzível permite verificar as vantagens,
os empates e os contraexemplos.

O tokenizer é real, mas **os erros são corrupções controladas de registros fictícios**.
Não houve inferência nem comparação com uma nova tentativa do modelo. Os casos
compartilham templates; 20 valores diferentes não são 20 mecanismos independentes.
Os intervalos de tempo são descritivos e não estimam prevalência de erros reais.
Nenhum desses resultados altera o resultado negativo anterior de geração completa.

No mês restante, a prioridade científica é coletar uma coorte congelada de saídas
reais, antes de ajustar o método, e compará-lo com validação + json_repair, esquema,
e uma nova tentativa do modelo. Usar o mesmo conjunto integral, contar respostas
já válidas e falhas, separar tempo/custo de inferência e reportar preservação de
dados. Isso amplia validade externa; não é necessário fingir que já foi medido
para defender a contribuição limitada obtida aqui.
