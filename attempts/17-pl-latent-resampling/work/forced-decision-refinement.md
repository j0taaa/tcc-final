# Eliminar sorteios determinísticos em todos os controles

Refinamento comum da referência, antes de uma nova medição. As versões anteriores
e todas as suas perdas permanecem acessíveis. Reavaliação dos oito critérios:

1. Uso: mesmas consultas iid/gradientes PL sob JSON/GLC; nenhum objetivo novo.
2. Significância: omitir uma categoria/moeda de probabilidade 1 é otimização
   clássica trivial, não contribuição científica. Evita medir trabalho inútil.
3. Adoção: aplicar igualmente à mistura, Base, Single, perfis e enumeração.
   Uma vantagem que desaparecer com isso não justifica escolher a mistura.
4. Prova: se uma alternativa tem toda a massa positiva de um nó, selecioná-la
   diretamente coincide com sua lei categórica; uma moeda 1 sempre aceita.
   Eliminar esses sorteios preserva a distribuição, não a sequência do PRNG.
5. Protocolo: os mesmos nove inputs/48 eventos, três repetições, lote 4096 com
   checkpoint 1024, mesmos limites. Repetir as seis entradas neurais por hash.
   **A geração dos eventos nativos de bulk mantém o sampler antigo**, com o
   flag false: ordem/evidência não podem mudar porque se consumiram menos bits.
   As consultas condicionais usam o flag true; os dados verificarão a igualdade
   das evidências com v4. Não escolher apenas o evento que favoreceu a mistura.
6. Custo: toda preparação/cache/aritmética/compilação continua contabilizada.
   Registrar decisões determinísticas eliminadas na memória lógica; não RSS.
7. Objeção: outra implementação pode ser ainda melhor. Não chamar essa
   referência de solver mais rápido possível, nem inferir convergência/GPU.
8. Artigo: manter separados correção, benefício da operação e ganho do kernel.
   Anterioridade e revisão humana continuam sem confirmação.

O programa v4 continua até completar sua grade. O novo comportamento é opt-in
(--fast-forced) e não altera processos já iniciados nem experimentos antigos.
A amostragem do modelo no estudo neural usa o backend mantido, inalterado.
