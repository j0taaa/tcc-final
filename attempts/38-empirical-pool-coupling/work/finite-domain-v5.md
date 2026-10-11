# A38: explicit finite-domain consequence of the minimax proof

2026-10-11. New corollary of v3, written before native application code.
For a domain with M>=3 allowed distinguishable canonical keys, v3's
finite bound gives, with beta=b-2 in[0,2],

    rho_opt <= (M-2)*(M*beta+1)/(8*(M-1)^2)+5/(4M)
             = beta/8 +(M-2-beta)/(8*(M-1)^2)+5/(4M)
             <= beta/8 +11/(8M).

The last inequality uses M*(M-2)<=(M-1)^2 and beta>=0. The constructive
mixture always has rho>=beta/8. Consequently its worst-case fraction is
within11/(8M) of the optimum even for a fixed finite domain. This removes
the need to misapply an infinite-alphabet limit to a finite tokenizer.
It is an ADDITIVE approximation in the guaranteed fraction, not a bound
on a particular prompt's latency, semantic accuracy or informed optimum.

For b=3 the practical implementation uses one exact fair coin. For other
rational budgets, its known mixture probability is a rational coin; no
unknown-P approximation is needed. For an arbitrary real b the supremum
statement can use rational mixture probabilities approaching(b-2)/2 from
below; literal computational attainment is asserted only when that known
coin is implementable. The v3 probabilistic-kernel formulation remains
valid with an ideal independent uniform source.

The lower bound still ranges over arbitrary oracle laws on that domain.
It is NOT automatically a lower bound for a restricted family of neural
distributions or a decoder exposing its complete source/conditional logits.
Large output cardinality by itself does not establish scientific novelty.
