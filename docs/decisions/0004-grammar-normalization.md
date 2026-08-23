# ADR 0004: controlled grammar normalization

- Status: accepted
- Date: 2026-08-23

## Context

The token-aligned CKY solver requires strict terminal/binary CNF: `A -> a`
and `A -> B C`, plus an explicit empty-string flag. The pinned EPIC binding
offers `CFG.to_normal_form()`, but its Python API exposes serialized productions
rather than stable production identities or origin mappings.

We audited the pinned upstream commit on epsilon, unit-cycle, recursive, and
ambiguous fixtures. Bounded Boolean enumeration through length four found no
language disagreement. However, the returned epsilon fixture retained a
non-start epsilon production and the returned unit fixture retained unit
productions and a unit cycle. Those shapes are not valid input to this CKY
implementation. The upstream output also cannot identify which original
production produced each rewritten rule.

## Decision

The Python reference path uses the controlled normalizer in
`mwpc_exact.reference.normalization`; it does not call upstream
`to_normal_form()` as an implementation step.

The controlled pipeline:

1. computes nullable nonterminals and records start-symbol empty acceptance;
2. removes epsilon bodies while retaining every non-empty nullable variant;
3. removes unit productions by deterministic transitive closure;
4. gives terminals in longer bodies synthetic nonterminals;
5. right-binarizes longer bodies with stable synthetic symbols; and
6. records source production IDs on every normalized production.

Duplicate normalized rules are merged as Boolean grammar alternatives, and
their source production IDs are combined. The diagnostic mapping is not a
claim that a source grammar has a unique derivation.

Empty-string acceptance is metadata on `CnfGrammar`. Epsilon never consumes a
finite token slot. The repository-CFG adapter remains a strict boundary and
rejects serialized unit productions, non-start epsilon, or bodies longer than
two instead of silently normalizing them.

## Consequences

- Reference-solver correctness does not depend on an opaque upstream rewrite.
- Normalized production IDs are stable for a fixed source grammar ordering.
- Bounded fixed-point enumeration tests independently compare source and CNF
  languages, including recursive and ambiguous cases.
- The EPIC normalizer remains audited as a baseline dependency but is not
  modified or treated as strict CNF.
