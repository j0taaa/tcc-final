# V8 — diagnóstico de conteúdo aceito antes do prefixo contíguo

## Decisão e fronteira

V7 falhou em TODOS os oito inputs: classes raiz variadas só se tornaram
observáveis depois de muito trabalho. Os256 prefixos e1845 forwards continuam
preservados, com produtor fe3fa65. Não iniciar qualidade para aquela escolha.
Esta é uma investigação nova e limitada de recursos, não sua confirmação.

O checkpoint agora é o PRIMEIRO evento nativo que aceita um novo token original
cuja emissão contém algum dígito ASCII. Examine somente posições de geração
antes mascaradas, depois efetivamente aceitas no canvas; não propostas brutas,
slots fornecidos pelo prompt, EOS ou MASK. Em lote, use a menor posição nova;
no token, o primeiro dígito. A GLC tem dígitos somente em números, não em
nomes de campos/operadores. Não se exige prefixo textual contíguo ou número
completo. A classe1 é dígito ímpar; classe0 é par OU término sem evento.
Nunca filtre falhas ou reamostre até encontrar um dígito favorável.

Paridade NÃO é acerto, semântica, verificador ou gold. Uma classe variada
pode ter sinal semântico zero. Este protocolo tenta eliminar a objeção de
custo antes de investir em testes de qualidade. Mesmo seu sucesso não
autoriza alegar utilidade, prioridade ou publicação.

## Oito critérios reavaliados antes de forwards

1. **Uso:** dois programas JSON recursivos para a mesma pergunta, consumidos
   por um interpreter, gerados pela LLaDA/EPIC nativos. A operação futura
   seria diversidade de candidatos com marginais individuais preservadas.
   Este diagnóstico NÃO executa ainda esse par nem um comparador competitivo.
2. **Relevância:** a fronteira sample-only A34 é uma candidata matemática
   delimitada; ingredientes de estratificação/antítese/ruína/estimação
   sequencial são conhecidos. Trocar o checkpoint é engenharia, não novidade.
   Suficiência acadêmica e prioridade específica continuam abertas.
3. **Escolha:** só vale investigar uma classe observável cedo com continuação
   cara e efeito no resultado. Compare depois com iid com mais candidatos,
   mistura iid, caches completos, ruídos antitéticos/estratos, pools e política
   nativa integral. Nenhum controle é substituído por iid2 fraco neste screen.
4. **Prova:** a matemática A34 é independente do parser/modelo para o oráculo
   admitido. Paridade não prova benefício estrito sem diferença das médias
   condicionais; contar recursos não demonstra menor latência completa.
5. **Experimento:** mesmos TODOS oito inputs de treino selecionados só pelo
   hash, mesmos limites/modelo/política,32 seeds novas por input. Sem gabaritos
   ou corpus de confirmação. Critérios de variedade/custo são os mesmos deV7:
   pelo menos3 de cada classe, pelo menos2 forwards novos na primeira cauda,
   custo médio de prefixo após o único forward comum no máximo custo daquela
   cauda EM wall E CPU; pelo menos2/8 casos para continuar esta direção.
   O primeiro tail é diagnóstico de recursos, não estimador de qualidade.
6. **Custo:** mesmo forward inicial em cache, cópia de canvas/IDs, classificação,
   RNG, parsing, fechamento de auxiliares e continuação literal cobrados.
   Double-CNF é o mesmo workaround comum do deadlock preservado, não alteração
   do vendor. Carga/setup são reportados à parte; não concorram jobs pesados.
7. **Objeção:** classes podem ser degeneradas ou semanticamente inúteis, o
   checkpoint pode ser tarde, caches competentes ou iid extra podem vencer.
   Screen negativo bloqueia campanha de qualidade desta configuração; positivo
   só remove uma objeção de recursos, sem garantir vitória/publicabilidade.
8. **Artigo:** faltam significância/novidade, sinal e comparação completa
   independente; revisão humana não ocorreu. Não alterar o artigo principal
   nem chamar este refinamento uma conquista.

## Reprodução e limites

Antes das capturas, commit completo dos fontes/configuração e push normal.
O producer verifica bytes contra o commit fornecido e publica seus hashes.
Comando opt-in: `PYTHONPATH=vendor/EPIC-Decoding:. .venv-live/bin/python -m
attempts.34-oracle-diversity-frontier.work.arithmetic_diagnostic_v7
--protocol arithmetic-protocol-v8 --source-commit HASH --output PATH`.
Não sobrescrever evidência nem atribuir novos dados ao producer V7. Falhas,
recusas, classe ausente e eventos incompletos permanecem. Recuperação externa
autocomplete ainda ausente neste diagnóstico; obrigatória igualmente nos
controles numa avaliação de geração completa.
