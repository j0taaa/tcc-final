# Ranking barato e avaliação cara são antecedentes, não uma aplicação nova

2026-10-11, depois do freezeV8 e sem alterar seu produtor.
[Jafari Jozani/Perron, original institucional](https://www.usherbrooke.ca/mathematiques/fileadmin/sites/mathematiques/documents/Recherche/Publications/Rapports_de_recherche/rr64.pdf),
Seções1--4 e respectivos argumentos foram lidos diretamente. A versão
publicada é2011, confirmada no [publisher](https://link.springer.com/article/10.1007/s13171-011-0004-2);
a data de indexação do PDF não data a descoberta. O problema já separa
ranking barato de medição cara. A amostragem antitética seleciona n elementos
de n² observações ordenadas; Teoremas2.1/3.1/4.1 demonstram imparcialidade e
comparações de variância. Para n2, escolhe ranks(1,4) ou(2,3), equiprováveis.
Portanto motivação de dois custos, seleção sem conhecer a distribuição,
estratificação empírica e redução de variância não são novas aqui.

## Especialização própria para confrontar o candidato, não reproduzir ciência

Considere quatro bits iidBern(p), desempate aleatório entre iguais e permute
aleatoriamente os dois outputs selecionados. Cada rank tem probabilidade1/2
de inclusão, e cada posição de output recebe cada rank com probabilidade1/4;
assim as marginais sãoBern(p). Um pool com três uns produz11 com chance1/2,
com quatro uns sempre, e com zero/um/dois nunca. Logo

    J11 = (1/2)4p³q + p⁴ = p² − p²q²;
    delta_pool4 = [p(1-p)]².

Esta é precisamente a lei ótima de orçamento fixo4 discutida emA32 e no
antecedente Nacu–Peres. NÃO atribuir novidade ao pool, lei ou sua otimização.
R3 não truncado tem delta=z²/(1-z), estritamente maior para0<p<1, e
esperança3 draws em vez dos4 de um pool que sempre materializa o lote.
Isso NÃO prova domínio de custo sobre controles competentes: o walk4 com
poda segura tem esperança3-z, MENOR queR3; pode também usar pools em paralelo.
Sua lei continua delta=z². Uma comparação completa precisa incluir esse
controle adaptativo, limites de cauda distintos, iid com mais outputs,
caches fortes e métodos com informação sobre probabilidades/ruídos.

Para ANY pontuação comum f e classificações binárias, o lift condicional
compara a variância por delta*(mu1-mu0)²; sinal zero dá vantagem zero.
Maior delta por si só não implica melhor custo/resultado de uma trajetória,
e não resolve a insuficiência prática dos dois checkpoints medidos.
Somente a fronteira sample-only esperada, com seu lower bound e attainability,
continua diferença candidata a conferir. Antecedentes de ranking fortalecem
a objeção à novidade da aplicação, não uma declaração de publicabilidade.
