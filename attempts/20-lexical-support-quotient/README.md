# Tentativa 20 — Suporte de tokens agrupado pelo efeito lexical completo

**Resultado negativo preservado:** 864 registros MDLM/CUDA, 795 completos,
744 comparações iguais, 0/18 ganhos predeclarados da candidata primária
e da secundária contra controles igualmente lexicais. Nenhuma divergência.
O lexer reduziu custo comparado à representação byte, mas é antecedente conhecido;
o quociente global não comprovou vantagem adicional. Não relaxar o critério.
Dados e análises em work/evidence/development-decision.md.
Fontes independentes de19 (`f675fe3`), sem importar work de outra tentativa.
A versão19 negativa fica preservada. Nenhum decoder mantido é substituído.

1. **Uso:** preenchimento de JSON recursivo com dLLM e novos top16 a cada
   forward. Novas palavras em strings frequentemente mudam conteúdo, mas não
   estrutura. Agrupar pelo efeito em TODOS os estados do lexer permite reutilizar
   a estrutura quando entram palavras novas equivalentes, sem alterar original
   token ID, modelo, probabilidades, compromissos ou fallback mínimo original.
2. **Relevância:** separar lexer/parser é clássico; DOMINO/SynCode/XGrammar
   já usam pré-processamento lexical. FactorDLM Proposição2 já prova quociente
   de classes para fatores invariantes. NÃO reivindicamos esses princípios.
   Candidata: construção automática, preservando fronteiras BPE arbitrárias e
   slots originais, de uma representação gramatical reutilizável sob expansão
   do suporte e contexto bilateral da dLLM. Pode ser apenas engenharia conhecida;
   precisa vantagem real frente ao lexer sem quociente e controles fortes.
3. **Escolha:** reduzir estrutura e reconstruções mantendo exatamente a mesma
   trajetória gulosa. Controles byte: GAC/SAT/root/Rust especulativo; controles
   lexer sem classes: GAC/SAT/root/especulativo. TODOS recebem a representação
   lexical quando apropriado; métodos clássicos por classes também entram,
   incluindo reservas64/128 inativas. Benefício de representação não implica
   que class_monotone supera os outros métodos por classes.
4. **Matemática:** equivalência de tokens exige mesma transição/saída para
   TODO estado do transdutor, não apenas o prefixo atual. Por composição,
   qualquer troca dentro da classe preserva toda cadeia lexical e validade
   CFG, mesmo em lacunas no meio e UTF8/escape repartidos. Expansão dentro das
   classes já ativas não altera o circuito. Prova/custo em specification.md;
   aplicação direta de congruência e quociente conhecidos, não novo teorema geral.
5. **Protocolo:** antes dos modelos, mesmos documentos externos e máscaras,
   sem injeção de gabarito. Dezesseis controles/configurações, todos os fracassos.
   Ganho>=20% wall E CPU contra TODOS os controles sem classes, sinal em cada
   repetição. Para confirmação, seis documentos nunca-model-testados, nove
   repetições e CPU/GPU. Comparação entre métodos com classes também registrada.
6. **Custo:** classificar todos os estados de cada token visto, agregar suportes,
   construir grafo/gramática/circuito, atualizar grupos/minima, recomputar se
   classe nova, escolher e expandir IDs, validar, TODOS os forwards e limpeza.
   Lexer/tabela do vocabulário não pré-calculados gratuitamente antes do relógio.
   Modelo e gramática fixos em serviço preparado têm startup registrado.
7. **Objeção:** lexicalização sem classes pode ganhar; controles por classes
   podem executar melhor; FactorDLM com boa partição obtém a mesma redução.
   Classes muito finas, gramáticas que distinguem nomes/literais ou custo de
   modelo dominante podem eliminar economia. Escopo inicial é sintaxe JSON
   completa, não JSON Schema geral ou qualidade semântica. Não usar só vantagem
   contra byte CFG como novidade, pois lexicalização já é estabelecida.
8. **Artigo:** faltam utilidade completa confirmada, delimitação da diferença
   própria e revisão humana. Provas escritas, testes independentes e medições
   devem ser separados. Não basta compilar, dar exemplo ou alegar prioridade.

Antecedentes primários conferidos:
[SynCode §§4.3–4.6](https://arxiv.org/html/2403.01632v3),
[DOMINO §§3.2–3.4](https://arxiv.org/abs/2403.06988),
[XGrammar](https://arxiv.org/abs/2411.15100),
[FactorDLM Proposição2](https://arxiv.org/html/2609.32900v1),
[Quimper–Walsh](https://arxiv.org/pdf/0903.0470).
Nenhum deles é substituído por implementação deliberadamente fraca.
