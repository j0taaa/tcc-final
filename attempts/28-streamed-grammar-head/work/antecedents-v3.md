# Auditoria adicional antes dos timings —2026-10-11

- [FactorDLM, Proposição2 e ApêndiceD.2](https://arxiv.org/html/2609.32900v1)
  enuncia explicitamente MAP, partição e amostragem exatas via classes e
  expansão interna. Portanto, a lei do resumo A28 também é consequência
  direta deste antecedente; não somente de FlashSampling. A investigação
  restante é uma implementação de comunicação/aritmética para CFG recursiva,
  não um novo teorema de quociente. O artigo também usa operações float64
  residentes em CUDA. Evitar apresentar GPU por si só como novidade.
- [SIMPLE, §5.3/9](https://arxiv.org/html/2512.00719v1) já desagrega sampling
  GPU/CPU, soma massas de grupos hot/tail e corrige propostas por rejeição.
  Extensão gramatical está entre as direções futuras, mas isto não reserva
  novidade a A28. Contagem de bytes e benefício em serviço real são obrigações
  independentes; não comparar tempos reportados em outra máquina.
- [Goodrich/Eldawy, SPAA2016](https://www.cs.ucr.edu/~eldawy/publications/16_SPAA.pdf)
  já usam representação alternativa para soma exata sem propagação de carry
  intermediária. A redução positiva de32 bits em A28 não é um novo princípio.
- [Iakymchuk/Defour/Collange/Graillat, ITNG2015](https://perso.lip6.fr/Stef.Graillat/papers/ITNG2015.pdf)
  tem título *Reproducible Triangular Solvers for High-Performance Computing*,
  aplica soma multi-nível exata/superacumuladores em GPU. A referência abreviada
  a ExBLAS no addendum v2 aponta a esse antecedente, não a um artigo novo nosso.
- GSP README primário foi recuperado via API GitHub no commit
  `30a9d0ed82f26dc53ec74b4f0985e1d213a18625`. Confirma projeção restrita conhecida
  e pequenas diferenças numéricas entre ordens de redução. Nada do seu código
  foi incorporado e seus tempos não foram reproduzidos. A ficha v1 registra
  o acesso inicialmente incompleto e permanece preservada no snapshot.

**Conclusão anterior à medição:** nenhuma novidade matemática suficiente foi
encontrada nesta direção. Um possível artigo de sistemas precisa mostrar
uma fronteira exata útil frente a controles vetorizados, custos completos,
aplicação neural real e diferença técnica bem localizada. Vantagem de consulta
isolada não confirma publicação nem vitória sobre EPIC; perdas eliminam a
promoção dessa hipótese. A revisão não é revisão humana independente.
