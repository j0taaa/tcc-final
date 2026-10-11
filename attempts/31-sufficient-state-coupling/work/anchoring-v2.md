# A31v2 — Ancoragem exata na primeira geração nativa

Critérios do README v1 continuam válidos; este refinamento acrescenta o uso
de retry sem alterar literalmente o primeiro resultado do EPIC. Condicionar
estratificação numa partícula retida é antecedente, não novidade: Chopin e
Singh2015, *On particle Gibbs sampling*, doi10.3150/14-BEJ629, seção5,
https://arxiv.org/html/1304.1887v2. Ali, resampling atualiza genealogias de um
filtro condicionado; aqui retém-se o ruído observado de um decoder congelado,
sem trocar sua lei individual ou fazer resampling das trajetórias. Esta
diferença operacional não confirma prioridade por si só.

## Lema de ancoragem finita

Um ticket original I é uniforme em {0,...,W-1}. Independente dele, sorteie
D uniforme em {0,...,K-1}. Defina Z=K I+D, S=floor(Z/W), R=Z mod W. Então Z
é uniforme em {0,...,KW-1}; (S,R) tem exatamente a lei estrato uniforme ×
resíduo uniforme, e floor((S W+R)/K)=I. Portanto pode-se atribuir S ao primeiro
visitante observado, guardar I sem modificá-lo, e sortear os estratos dos
visitantes seguintes sem reposição. A lei conjunta é igual à versão v1.

A identidade vale também quando W<K ou K não divide W. A ordem do primeiro
visitante depende só de ancestrais, não do ruído ainda não observado. O resto
do tensor de ruído permanece independente. A combinação com as provas v1
preserva as garantias; nenhum novo forward ou draw Torch é necessário.
A primeira trajetória serial só encontra tabelas novas e conserva todo seu
ruído original. Logo conserva IDs/rejeições/EOS e chamadas do EPIC nativo,
com mesma seed, modelo determinístico e ausência de interrupção por relógio.

## Perfil CUDA

CPU permite recuperar Z53=I diretamente de U=I/2^53. CUDA produz
RN(I/2^53+2^-54), trocando1 por0. Na metade superior alguns U têm dois
pré-imagens de tickets, igualmente prováveis; reconstruí-los exige sortear
o posterior uniforme entre ambos, não simplesmente arredondar U·2^53.
U=0 é a pré-imagem2^53-1, U=0.5 tem uma pré-imagem. Na metade inferior há
pré-imagem única. A implementação verifica a transformação de cada ticket
compatível antes de escolher. O RNG do ledger é separado do RNG do Torch.

## Limites e validação necessária

Continua sendo estratificação de UMA coordenada opaca, com todas as decisões
restantes e recuperação originais. Não promete ganho semântico relevante,
latência menor ou publicação. Testar lei conjunta por enumeração independente
com todos os tamanhos pequenos, transcrição literal da primeira geração em
CPU/CUDA e os extremos de arredondamento. Medir root-only/histórico/estado
na aplicação externa com custos completos e regras congeladas.
