# V2 — Exact seven-row obstruction, before its new checker

2026-10-17. AFTER V1's SINGLE solve exits2/numerically infeasible, BEFORE
new certificate/checker execution. V1 source and record stay unchanged.
This is a rejection of the proposed primary benefit, not a relaxed target.

## The conjecture was false

V1 correctly observed that completions ABCDBB/ABCDCC/ABCDDD force incompatible
partners for a per-tape control. I overlooked that the same zero coefficients
also forbid early stopping in a population-law algorithm. Its Bernstein
terminal constraints are averages of NONNEGATIVE output probabilities. If the
conditional target puts zero mass on a class, every ordered tape in that
multiset must have zero output probability on that class. Population-law
preservation cannot escape this particular obstruction.

For the multiset A+3B+C+D, the classical minimum-repeat matching pairs EVERY
singleton with B. Given first A, the terminal partner must therefore be B,
individually on each order of the remaining3B+C+D. Prefix ABCD followed by BB
cannot have stopped with C or D. Reassigning which of its three nonfirst keys
is tripled forbids every nonfirst output at ABCD. Thus a universal rule for
this fixed target CANNOT stop on four distinct keys at length four.
The same argument applies to every anonymous ordering and, by renaming keys,
to every such actual prefix. No exact25% diffuse-limit gain of V1 is possible.

## Farkas certificate for the ORIGINAL V1 LP

Use its normalized variables/rows, with x>=0 and Ax=b. Let E2,E3 be the
endpoint rows `end:1,3,1,1:2` and `end:1,3,1,1:3`. Both have RHS zero.
Their coefficients are averages over the20 distinct named tails3B+C+D.
The following row combination is exact:

    y(root)=-1,
    y(flow:01)=y(flow:012)=y(flow:0123)=-1,
    y(distinct4)=1,
    y(E2)=y(E3)=5,
    all other y=0.

The root/flow/distinct part has RHS-1 and left side

    -s_01,1 -s_012,1 -s_012,2
    -s_0123,1 -s_0123,2 -s_0123,3.

All continuation coefficients cancel. E2+E3 has coefficient2/5 on s_01,1,
2/5 on each s_012,j and1/5 on each s_0123,j. Their fivefold sum covers every
displayed negative coefficient. All other coefficients are nonnegative.
Consequently

    y A >=0 componentwise, y b=-1<0.

There is no feasible nonnegative x: yAx>=0 cannot equal yb. This is a written
Farkas certificate, not reliance on HiGHS's infeasibility message. The new
stdlib checker must independently enumerate the20 named tails and15 perfect
matchings, reconstruct these seven rows, check the signs/RHS, and compare
them with an exact export of the ORIGINAL frozen V1 producer. No new solve.
Reject a missing positive endpoint contribution and a wrong root sign.

## Consequences and eight-criteria decision

Retaining V1's assumptions, N>=5 on every all-distinct full tape. The strong
per-tape control has mean16/3 there, so any possible population-law saving
relative to it is at most1/16=6.25%, NOT the25% primary conjecture. This is an
UPPER limit, not an achieved saving or an all-P latency statement. V1's
conditional diffuse corollary never becomes an unconditional theorem.

Criteria2/3/4/5 now REJECT the proposed four-draw benefit by an exact written
obstruction. Criteria1/6/8 were already open: no real consumer, full-cost
benefit or sufficient priority established. Matching/coefficient/Farkas
principles are classical. This negative audit does NOT satisfy the user's
positive goal. No replacement five-draw search, changed kernel, relaxed gate,
new cap, neural campaign or old failed consumer is triggered. The three-class
A63 theorem stays intact; it never has a four-distinct prefix. Preserve this
direction and investigate a substantively different useful consequence.
