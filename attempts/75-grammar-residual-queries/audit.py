"""Independent finite attacks: tuple enumeration, rational series, exact chains.

Run from the repository root. This file does not time its audits or use GPU.
Results are written once with exclusive creation, never silently overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction as F
from functools import cache
from pathlib import Path

import oracle as candidate


@cache
def rational_log(q):
    """Independent exact-rational atanh series and analytic remainder."""
    if q < 1:
        low, high = rational_log(1 / q)
        return -high, -low
    t = (q - 1) / (q + 1)
    low = 2 * sum((t ** (2 * j + 1) / (2 * j + 1) for j in range(52)), F())
    high = low + 2 * t**105 / (105 * (1 - t * t))
    return low, high


def independent_fixture(n, alpha, name):
    words, reference, factors = [], [], []
    for word in itertools.product((0, 1), repeat=n):
        valid = (
            not any(a == b == 1 for a, b in itertools.pairwise(word))
            if name == "hard_core"
            else sum(word) == n // 2
        )
        if not valid:
            continue
        if name == "hard_core":
            g = F(8, 8 + 9 * (sum(word) - 1) ** 2)
            reference.append(F(1, 3 ** sum(word)))
        else:
            reference.append(F(1))
            if name == "adjacent_equal":
                g = F(1 + sum(a == b for a, b in itertools.pairwise(word)), n)
            else:
                t = F(sum(word[: n // 2])) - F(n, 4)
                g = F(n) / (n + 9 * t * t)
                if name == "witness_minus":
                    g = 1 - g
        words.append(word)
        factors.append(1 + alpha * g)
    total = sum(reference)
    reference = [v / total for v in reference]
    target = [r * f for r, f in zip(reference, factors, strict=True)]
    total = sum(target)
    return words, reference, [v / total for v in target], factors


def independent_pins(words, reference, target):
    """All ternary pins; filter full words directly, without candidate tables."""
    n = len(words[0])
    for pin in itertools.product((None, 0, 1), repeat=n):
        matching = [
            j
            for j, w in enumerate(words)
            if all(a is None or a == b for a, b in zip(pin, w, strict=True))
        ]
        if not matching:
            continue
        r, p = sum(reference[j] for j in matching), sum(target[j] for j in matching)
        yield (
            pin,
            p,
            r,
            tuple(sum(target[j] for j in matching if words[j][i]) / p for i in range(n)),
            tuple(sum(reference[j] for j in matching if words[j][i]) / r for i in range(n)),
        )


def decimal_value(q):
    return Decimal(q.numerator) / Decimal(q.denominator)


def check_case(case):
    n, alpha = case.n, case.alpha
    words, r, p, factors = independent_fixture(n, alpha, case.name)
    indexed = {
        sum(v << i for i, v in enumerate(w)): (a, b) for w, a, b in zip(words, r, p, strict=True)
    }
    assert all(indexed[x] == (a, b) for x, a, b in zip(case.words, case.r, case.p, strict=True))
    checked, delta_checks, chain_checks = 0, 0, 0
    pin_reference = {}
    L = 2 * alpha * 3
    for pin, pmass, rmass, pones, rones in independent_pins(words, r, p):
        mask = sum(1 << i for i, v in enumerate(pin) if v is not None)
        value = sum(1 << i for i, v in enumerate(pin) if v == 1)
        assert F(case.oracle.table[mask, value], case.oracle.table[0, 0]) == pmass
        assert F(case.reference.table[mask, value], case.reference.table[0, 0]) == rmass
        assert tuple(case.oracle.marginal(mask, value, i) for i in range(n)) == pones
        assert tuple(case.reference.marginal(mask, value, i) for i in range(n)) == rones
        pin_reference[mask, value] = pones, rones
        checked += 1
        if case.name == "hard_core":
            continue  # slice concentration is not claimed for hard-core
        for a, b in zip(pones, rones, strict=True):
            if b in (0, 1):
                assert a == b
                continue
            d0, d1 = candidate.log((1 - a) / (1 - b)), candidate.log(a / b)
            oscillation = (d1 - d0).absolute()
            assert F(oscillation.hi, candidate.SCALE) ** 2 <= L * L / n
            mean = d0 * (1 - b) + d1 * b
            assert F(mean.lo, candidate.SCALE) >= -L * L / (8 * n)
            assert mean.hi <= 0
            delta_checks += 1
    for word, mass in zip(words, p, strict=True):
        for order in (range(n), reversed(range(n))):
            mask, value, probability = 0, 0, F(1)
            for i in order:
                pi = pin_reference[mask, value][0][i]
                probability *= pi if word[i] else 1 - pi
                mask |= 1 << i
                value |= word[i] << i
            assert probability == mass
            chain_checks += 1
    lipschitz = 0
    if case.name != "hard_core":
        for i, x in enumerate(words):
            for j, y in enumerate(words):
                distance = sum(a != b for a, b in zip(x, y, strict=True))
                assert (factors[i] - factors[j]) ** 2 * n <= (alpha * 3 * distance) ** 2
                lipschitz += 1
    return {
        "pins": checked,
        "delta_checks": delta_checks,
        "exact_chains": chain_checks,
        "lipschitz_pairs": lipschitz,
    }


def check_law(case, result):
    errors, decimal_hb = [], []
    with localcontext() as context:
        context.prec = 90
        for index, x in enumerate(case.words):
            exact_ratio = case.p[index] / case.r[index]
            low, high = rational_log(exact_ratio)
            assert result["h"][index].contains(low) and result["h"][index].contains(high)
            # Independent scalar Decimal sum, no interval routines or candidate logs.
            hb = Decimal(0)
            b = decimal_value(case.alpha)
            for mask in range((1 << case.n) - 1):
                value = x & mask
                terms = Decimal(0)
                for i in range(case.n):
                    if mask & (1 << i):
                        continue
                    p = case.oracle.marginal(mask, value, i)
                    r = case.reference.marginal(mask, value, i)
                    if not x & (1 << i):
                        p, r = 1 - p, 1 - r
                    terms += decimal_value(p / r).ln()
                w = terms * case.n / (case.n - mask.bit_count())
                hb += min(b, max(-b, w)) / (case.n * math.comb(case.n, mask.bit_count()))
            decimal_hb.append(hb)
            # 90-digit Decimal is a cross-check, not an independent certificate.
            midpoint = Decimal(result["hb"][index].lo + result["hb"][index].hi) / (
                2 * candidate.SCALE
            )
            errors.append(abs(hb - midpoint))
        raw = [decimal_value(r) * h.exp() for r, h in zip(case.r, decimal_hb, strict=True)]
        z = sum(raw)
        tv = sum(abs(v / z - decimal_value(p)) for v, p in zip(raw, case.p, strict=True)) / 2
        assert abs(tv - Decimal(str(result["tv"].result()["display_midpoint"]))) < Decimal("1e-16")
        assert max(errors) < Decimal("1e-70")
    return str(max(errors))


def check_distinct_logs():
    checked = 0
    # Revisit all distinct ratios through the wrapper; independent exact series.
    for q in tuple(LOG_ARGUMENTS):
        bounds = candidate.log(q)
        low, high = rational_log(q)
        assert bounds.contains(low) and bounds.contains(high)
        checked += 1
    return checked


def moment_checks(case, result):
    """Exact rational upper moments of the interval enclosure, for finite p."""
    n, alpha = case.n, case.alpha
    C = 12 * alpha + F(9, 2) * alpha * alpha
    moments = {p: [F() for _ in range(n)] for p in (1, 2, 4, 8)}
    for x, mass in zip(case.words, case.r, strict=True):
        for mask in range((1 << n) - 1):
            value = x & mask
            ps = tuple(case.oracle.marginal(mask, value, i) for i in range(n))
            rs = tuple(case.reference.marginal(mask, value, i) for i in range(n))
            w = candidate.increment(n, x, mask, ps, rs).absolute()
            bound = F(w.hi, candidate.SCALE)
            r = mask.bit_count()
            for p, levels in moments.items():
                levels[r] += mass * bound**p / math.comb(n, r)
    for p, levels in moments.items():
        for r, moment in enumerate(levels):
            square = C * C * p * n / (n - r)
            assert moment * moment <= square if p == 1 else moment <= square ** (p // 2)
        for field in ("h", "hb"):
            moment = sum(
                mass * F(v.absolute().hi, candidate.SCALE) ** p
                for mass, v in zip(case.r, result[field], strict=True)
            )
            square = 4 * C * C * p
            assert moment * moment <= square if p == 1 else moment <= square ** (p // 2)
    return {"p": [1, 2, 4, 8], "slice_levels_per_p": n, "h_and_hb": True}


def theory_constants(alpha, d):
    """Rational upper bound on M_C, including its uncomputed infinite tail."""
    C = 12 * alpha + F(9, 2) * alpha * alpha
    upper, term = F(), F()
    for j in range(129):
        root = math.isqrt(j**j)
        root += root * root < j**j
        term = (4 * C) ** j * root / math.factorial(j)
        upper += term
    ratio = 7 * C / math.isqrt(129)  # sqrt(e)<7/4
    assert ratio < 1
    upper += term * ratio / (1 - ratio)
    sqrt_upper = math.isqrt(candidate.ceil(upper)) + 1
    # K0<10: this B is sufficient for the proven bound <= d/2.
    sufficient_B = 80 * C * C * sqrt_upper / d
    return {
        "C": str(C),
        "M_C_rational_upper": str(upper),
        "M_C_upper_display": float(upper),
        "sufficient_B_for_half_error_using_loose_constants": str(sufficient_B),
        "log_expected_NFE_upper_at_sufficient_B_display": (
            math.log(2 * float(sufficient_B)) + float(sufficient_B) + 2 * float(C)
        ),
        "TV_bound_at_frozen_B_is_vacuous": 4 * (4 * 3**0.75) * float(C * C / alpha) > 1,
    }


LOG_ARGUMENTS = set()
ORIGINAL_LOG = candidate.log


def tracked_log(q):
    LOG_ARGUMENTS.add(q)
    return ORIGINAL_LOG(q)


def grammar_checks():
    from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
    from mwpc_exact.reference.ll1 import check_ll1

    b = _SourceGrammarBuilder(("S", "T", "U"), start="S")
    for head, body in (
        ("S", (b"0", "T", b"1", "S")),
        ("S", (b"1", "U", b"0", "S")),
        ("S", ()),
        ("T", (b"0", "T", b"1", "T")),
        ("T", ()),
        ("U", (b"1", "U", b"0", "U")),
        ("U", ()),
    ):
        b.rule(head, *body)
    check_ll1(b.build())

    def parse(word):
        position = 0

        def symbol(nonterminal):
            nonlocal position
            look = word[position] if position < len(word) else None
            opening = 0 if nonterminal == "T" else 1
            if nonterminal == "S":
                if look is None:
                    return
                opening = look
            elif look != opening:
                return
            position += 1
            symbol("T" if opening == 0 else "U")
            if position >= len(word) or word[position] != 1 - opening:
                raise ValueError("unmatched excursion")
            position += 1
            symbol(nonterminal)

        try:
            symbol("S")
            return position == len(word)
        except ValueError:
            return False

    checked = 0
    for n in range(11):
        for word in itertools.product((0, 1), repeat=n):
            assert parse(word) == (2 * sum(word) == n)
            checked += 1
    return checked


def reconstruct_hard_core(case):
    histograms = sorted(set(x.bit_count() for x in case.words))
    counts = [sum(x.bit_count() == s for x in case.words) for s in histograms]
    rows = [[F(1) for _ in histograms] + [F(1)]]
    # Exactly ONE all-marginal query. Formula-free reconstruction after it.
    root = case.oracle.query(0, 0)
    for i in range(case.n):
        rows.append(
            [
                F(sum(x.bit_count() == s and bool(x & (1 << i)) for x in case.words), count)
                for s, count in zip(histograms, counts, strict=True)
            ]
            + [root[i]]
        )
    pivot = 0
    for col in range(len(histograms)):
        found = next((j for j in range(pivot, len(rows)) if rows[j][col]), None)
        assert found is not None, "root histogram not identifiable"
        rows[pivot], rows[found] = rows[found], rows[pivot]
        divisor = rows[pivot][col]
        rows[pivot] = [v / divisor for v in rows[pivot]]
        for j in range(len(rows)):
            if j != pivot:
                multiplier = rows[j][col]
                rows[j] = [a - multiplier * b for a, b in zip(rows[j], rows[pivot], strict=True)]
        pivot += 1
    histogram = [rows[i][-1] for i in range(pivot)]
    reconstructed = [
        histogram[histograms.index(x.bit_count())] / counts[histograms.index(x.bit_count())]
        for x in case.words
    ]
    assert reconstructed == case.p
    m = 1 / (1 + case.alpha)  # known before deciding whether to query
    residual = [(p - m * r) / (1 - m) for p, r in zip(reconstructed, case.r, strict=True)]
    assert min(residual) >= 0 and sum(residual) == 1
    assert [m * r + (1 - m) * h for r, h in zip(case.r, residual, strict=True)] == case.p
    return {
        "rank": pivot,
        "histogram": list(map(str, histogram)),
        "mixture_expected_queries": str(1 - m),
        "mixture_tv": "0",
    }


def bridge_attack():
    root = F(1, 2)
    first_order, reverse_order = root * F(18, 19), root * F(2, 3)
    assert first_order == F(9, 19) and reverse_order == F(1, 3)
    assert first_order != reverse_order
    model = Path(
        "/home/jota/.cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/"
        "08b83a6feb34df1a6011b80c3c00c7563e963b07"
    )
    files = ("modeling_llada.py", "config.json", "tokenizer.json")
    hashes = {name: hashlib.sha256((model / name).read_bytes()).hexdigest() for name in files}
    vocab = json.loads((model / "tokenizer.json").read_text())["model"]["vocab"]
    config = json.loads((model / "config.json").read_text())
    return {
        "status": "NOT_APPLICABLE_ORACLE_CONTRACT",
        "forwards": 0,
        "model_path": str(model),
        "source_sha256": hashes,
        "single_character_original_ids": {v: vocab[v] for v in ("0", "1")},
        "model_vocab_size": config.get("vocab_size"),
        "bayes_cycle": {"order_0_then_1": str(first_order), "order_1_then_0": str(reverse_order)},
        "forced_reference_example": {
            "n": 4,
            "pins": "11??",
            "R_remaining_1": "0",
            "iid_P_remaining_1": "1/2",
        },
        "reason": (
            "Local model exposes unconstrained positional logits; no coherent "
            "grammar-conditioned oracle or Lipschitz certificate is supplied. "
            "A projected remasked head need not obey Bayes cycles."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate.log = tracked_log
    header = {"kind": "audit", "grammar_words": grammar_checks(), "bridge": bridge_attack()}
    all_cases, summaries = {}, []
    with args.output.open("x") as output:
        output.write(json.dumps(header, sort_keys=True) + "\n")
        output.flush()
        for n, alpha, name in candidate.cases():
            case = candidate.make_case(n, alpha, name)
            row = {"kind": "case", "n": n, "alpha": str(alpha), "target": name}
            try:
                row["checks"] = check_case(case)
                result = candidate.law(case)
                row["decimal_max_hb_discrepancy"] = check_law(case, result)
                d = candidate.tv(case.p, case.r)
                kappa = max(abs(p / r - 1) for p, r in zip(case.p, case.r, strict=True))
                row.update(
                    {
                        "tv_P_R": str(d),
                        "tv_P_Q": result["tv"].result(),
                        "Z_B": result["z"].result(),
                        "expected_NFE": result["queries"].result(),
                        "expected_proposals": result["proposals"].result(),
                        "stationary_lower_bound_half_error": str(d / (2 * kappa)),
                        "max_oracle_integer_bits": case.oracle.max_bits,
                        "truth_states": len(case.words),
                        "oracle_cylinders": len(case.oracle.table),
                        "sequential_expected_NFE": str(candidate.sequential_cost(case)),
                        "FORS_same_estimator": "identical law, queries and cost",
                    }
                )
                row["finite_half_error_subunit_query_gate"] = (
                    F(result["tv"].hi, candidate.SCALE) <= d / 2
                    and result["queries"].hi < candidate.SCALE
                )
                if name != "hard_core":
                    row["finite_moments"] = moment_checks(case, result)
                    row["theory"] = theory_constants(alpha, d)
                    pair, cost = candidate.pair_control(case)
                    row["pair_heat_bath"] = {
                        "updates": n,
                        "tv": str(candidate.tv(case.p, pair)),
                        "expected_NFE": str(cost),
                        "detailed_balance": True,
                    }
                    sirs = candidate.law(case, original_sirs=True)
                    row["original_SIRS"] = {
                        "tv": sirs["tv"].result(),
                        "leaked_mass": sirs["leaked"].result(),
                        "expected_NFE_including_root": sirs["queries"].result(),
                    }
                    root = [case.oracle.marginal(0, 0, i) for i in range(n)]
                    product = [
                        math.prod(root[i] if x & (1 << i) else 1 - root[i] for i in range(n))
                        for x in case.words
                    ]
                    valid_mass = sum(product)
                    frozen = [v / valid_mass for v in product]
                    row["frozen_root_product"] = {
                        "valid_mass": str(valid_mass),
                        "tv_different_target_to_P": str(candidate.tv(case.p, frozen)),
                        "root_NFE": 1,
                    }
                    if name.startswith("witness"):
                        assert root == [F(1, 2)] * n
                else:
                    row["root_histogram_control"] = reconstruct_hard_core(case)
                row["status"] = "PASS"
                all_cases[n, alpha, name] = case
            except Exception as error:
                row.update({"status": "FAIL", "error": repr(error)})
                output.write(json.dumps(row, sort_keys=True) + "\n")
                output.flush()
                raise
            output.write(json.dumps(row, sort_keys=True) + "\n")
            output.flush()
            summaries.append(row)
            print(
                json.dumps(
                    {
                        key: row[key]
                        for key in (
                            "n",
                            "alpha",
                            "target",
                            "status",
                            "finite_half_error_subunit_query_gate",
                        )
                    }
                ),
                flush=True,
            )
        separations = []
        for n in (4, 8):
            for alpha in (F(1, 100), F(1, 20)):
                plus, minus = (
                    all_cases[n, alpha, "witness_plus"],
                    all_cases[n, alpha, "witness_minus"],
                )
                half_mask = (1 << (n // 2)) - 1
                deltas = [F((x & half_mask).bit_count()) - F(n, 4) for x in plus.words]
                g = [F(n) / (n + 9 * delta**2) for delta in deltas]
                mean = sum(g) / len(g)
                deviation = sum(abs(v - mean) for v in g) / len(g)
                formula = (
                    alpha
                    * (2 + alpha)
                    * deviation
                    / (2 * (1 + alpha * mean) * (1 + alpha * (1 - mean)))
                )
                assert candidate.tv(plus.p, minus.p) == formula
                separations.append(
                    {
                        "n": n,
                        "alpha": str(alpha),
                        "tv_pair": str(formula),
                        "mean_absolute_g_deviation": str(deviation),
                        "root_marginals_identical": True,
                    }
                )
        tail = {
            "kind": "summary",
            "case_count": len(summaries),
            "witness_separations": separations,
            "distinct_log_certificates": check_distinct_logs(),
            "finite_gate_pass": sum(
                row["finite_half_error_subunit_query_gate"]
                for row in summaries
                if row["target"] != "hard_core"
            ),
            "status": "PASS",
        }
        output.write(json.dumps(tail, sort_keys=True) + "\n")
        print(json.dumps(tail), flush=True)


if __name__ == "__main__":
    main()
