# Chamadas externas, contribuição e limites de uso

A extensão M25 mede chamadas com um argumento textual livre e até três
argumentos escalares, geradas por LLaDA-8B-Instruct real. O estudo complementa
o benefício limitado encontrado em M24 e não substitui seus resultados por
uma promessa de generalização.

O [protocolo](m25-external-protocol.md) seleciona casos somente pelos esquemas,
constrói candidatos pelo pedido e separa nomes de função entre desenvolvimento
e confirmação. Todos os 68 casos elegíveis permanecem: 26 de desenvolvimento e
42 de confirmação. As duas execuções de confirmação continuam representando
42 pedidos. A pontuação é de um verificador AST próprio, não o score oficial BFCL.

## Comparação externa

A confirmação completa contém 42 pedidos por oito políticas e duas execuções:
672 gerações, incluídas nos 928 registros de M25. Confiança 0,8 acerta 5/42 em
ambas, contra 15/42 do EPIC 32. As medianas totais são 36.157 e 4.610 ms.
A diferença primária é −23,81 pontos; o intervalo conservador de 95% é
[−46,37; 3,67]. Não há não inferioridade nem redução de latência nesse recorte.

EPIC 8 acerta 16/17 nas duas execuções, a 1.990 ms; MAP iterativo chega a 11/42,
a 1.162 ms. Orçamento 64 acerta 3/42 a 8.929 ms, e MAP de uma passagem 2/42
a 207 ms. Essas observações favorecem EPIC ou MAP iterativo para este conjunto,
com seu custo e objetivo próprios. [Tabela completa e pareamento](generated/m25-confirmation-paired-results.md).

A resposta aceitável está em 38/42 suportes. As quatro ausências são mantidas,
mas não explicam a maior parte dos erros. Confiança completa 41/42 chamadas;
guloso completa 24/42 e tem 18 timeouts na primeira execução. Não confundir
validade, conclusão, otimalidade por etapa e intenção correta. O inventário
completo conserva 868 gerações completas, 51 timeouts e nove limites de
reamostragem, além das observações de interrupção.

Relatórios regeneráveis incluem acurácia por repetição, validade, tempo total,
forwards, intervalos pareados, cobertura e todos os estados de falha. A tabela
principal não remove respostas ausentes do suporte. Os relatórios de componentes
separam construção, parsing, reconstrução e validação quando a instrumentação
permite; suas somas não devem ser apresentadas como cobertura de todo forward.

## Por que validade não basta

A gramática garante a forma representada, não que uma sequência de palavras seja
o nome solicitado ou que uma opção facultativa do esquema possa ser omitida no
pedido concreto. Por exemplo, `simple_python_35` pede um restaurante em Nova York
aberto até pelo menos 11 PM. O suporte textual/numeral não inclui a combinação
aceita `New York, NY` e 23 horas. Esse caso permanece como erro de cobertura;
o otimizador não pode recuperar valores que não foram representados.

Mesmo quando uma resposta está representada, maximizar concordância com
propostas marginais não equivale a escolher a chamada semanticamente correta.
Comprometer um token preserva uma conclusão gramatical, mas altera as previsões
futuras. A garantia por etapa não resolve essa questão de trajetória.

## Demonstração reproduzível

Oito tentativas reais estão arquivadas. Na primeira configuração, as quatro
políticas escolhem nomes errados com aspas internas e recebem buscas vazias.
Um acompanhamento explicitamente pós-hoc declara suporte sem aspas duplas
internas antes da execução, mantém múltiplos nomes candidatos e não altera
a construção do benchmark. Confiança, MAP iterativo e EPIC geram Belo Horizonte
e recebem localidades; orçamento 64 ainda produz busca vazia. Não há inferência
de superioridade a partir desse único pedido.

O replay padrão usa a chamada correta da política de confiança, produzida por
`e7f6b43`, com doze certificados conferidos e resposta API obtida em 30/09/2026.
As quatro tentativas iniciais de `128c584` e os quatro acompanhamentos ficam
preservados. [Inventário gerado](generated/m25-query-demo-results.md),
[política declarada e diagnóstico](m25-demo-followup.md).

A demonstração preserva as quatro políticas executadas sobre o mesmo pedido;
nenhuma tentativa malsucedida foi descartada. A AST e o suporte são verificados
antes de um GET público de geocodificação. O replay e a conferência de testemunhas
funcionam sem modelo e sem rede. Isso demonstra o caminho geração–validação–consulta,
sem provar acurácia populacional nem necessidade de usar uma dLLM para geocodificar.

## O benefício sustentado e a contribuição

M24 mantém a comparação secundária positiva: MWPC com orçamento quatro acerta
86/100 chamadas sintéticas contra 74/100 do EPIC com oito etapas, com medianas
926 e 968 ms. Normalizar o layout lexical aumenta EPIC a 78/100, deixando oito
pontos de diferença. São treze vitórias pareadas e uma derrota; o teste é
secundário, sem ajuste por comparações múltiplas. A comparação primária por
confiança é mais rápida que EPIC 24, mas não estabelece não inferioridade de
acurácia. [Resultados M24](m24-findings.md).

A contribuição implementada combina otimização de concordância por etapa,
proveniência dos tokens, slots físicos, bytes composicionais, EOS/PAD e
certificados conferidos por implementação independente. Os experimentos
identificam um ponto útil de custo/qualidade e os limites ao ampliar a tarefa.
Weighted CFG, inferência exata restrita e confiança têm antecedentes; o projeto
não reivindica inventá-los. [Limites de novidade](m25-novelty-boundaries.md).

Os resultados não justificam escolher MWPC automaticamente para qualquer chamada.
Catálogos pequenos admitem controles enumerativos baratos; o EPIC é um comparador
forte para geração lexical. Uma decisão de uso exige a tarefa, o custo e a
necessidade da garantia por etapa, não somente a existência de um certificado.

## Reproduzir e conferir

[Comandos M25](m25-reproduction.md), [consulta real/replay](m25-query-demo.md),
`docs/research/generated/m25-campaign-inventory.json` e os manifests dos brutos
registram configurações, comandos, hashes, revisões e commits produtores.
