"""Every count premise, every tiny word ratio and actual finite GPU proposal replay."""

import argparse
import hashlib
import itertools
import json
import subprocess
from fractions import Fraction as F
from math import prod
from pathlib import Path
from random import Random

import numpy as np
import torch

from .reference import ceiling
from .scalar_acceptance import acceptance
from .test_reference import fixture
from .ticket_sampler import TicketSampler

H, D = 1 << 64, 1 << 40


def probability(packet):
    return prod(
        (F(ceiling(end * H, a) - ceiling(start * H, a), H) for a, start, end in packet), start=F(1)
    )


def upper32(value):
    rounded = np.float32(value)
    if F(float(rounded)) < F(float(value)):
        rounded = np.nextafter(rounded, np.float32(np.inf))
    return F(float(rounded))


def snapshot(sampler, prepared):
    ctl = sampler.control
    return dict(
        graph=[x.cpu().tolist() for x in ctl.graph],
        members=sampler.engine.members.cpu().tolist(),
        pointer=sampler.engine.pointer.cpu().tolist(),
        token=prepared["token_cdf"].cpu().tolist(),
        block=prepared["block_cdf"].cpu().tolist(),
        edge=prepared["edge_cdf"].cpu().tolist(),
        ta=prepared["token_totals"].cpu().tolist(),
        ba=prepared["block_totals"].cpu().tolist(),
        ea=prepared["edge_totals"].cpu().tolist(),
        mass=prepared["frontend"]["class_upper"].cpu().tolist(),
        emass=prepared["edge_mass_upper"].cpu().tolist(),
        h=prepared["potentials"].cpu().tolist(),
        scales=prepared["scales"].cpu().tolist(),
        node_p=sampler.node_positions.cpu().tolist(),
        edge_p=ctl.positions.cpu().tolist(),
    )


def endpoints(cdf, start, index, end):
    return (cdf[end - 1], cdf[index - 1] if index > start else 0, cdf[index])


def word_packet(data, word):
    outgoing, targets, pointer, labels = data["graph"]
    state, packet = 0, []
    for p, token in enumerate(word):
        j = data["members"].index(token)
        cid = next(
            c
            for c in range(len(data["pointer"]) - 1)
            if data["pointer"][c] <= j < data["pointer"][c + 1]
        )
        e = next(
            e
            for e in range(outgoing[state], outgoing[state + 1])
            if cid in labels[pointer[e] : pointer[e + 1]]
        )
        packet.append(endpoints(data["edge"], outgoing[state], e, outgoing[state + 1]))
        b = next(b for b in range(pointer[e], pointer[e + 1]) if labels[b] == cid)
        packet.append(endpoints(data["block"], pointer[e], b, pointer[e + 1]))
        packet.append(
            endpoints(data["token"][p], data["pointer"][cid], j, data["pointer"][cid + 1])
        )
        state = targets[e]
    return tuple(packet)


def replay(data, source):
    outgoing, targets, pointer, labels = data["graph"]
    state, word, packet = 0, [], []

    def choose(cdf, start, end, parts):
        r = int(parts[0]) | int(parts[1]) << 32
        ticket = r * cdf[end - 1] >> 64
        j = next(j for j in range(start, end) if cdf[j] > ticket)
        packet.append(endpoints(cdf, start, j, end))
        return j

    for p, raw in enumerate(source):
        e = choose(data["edge"], outgoing[state], outgoing[state + 1], raw[0])
        b = choose(data["block"], pointer[e], pointer[e + 1], raw[1])
        cid = labels[b]
        j = choose(data["token"][p], data["pointer"][cid], data["pointer"][cid + 1], raw[2])
        word.append(data["members"][j])
        state = targets[e]
    return tuple(word), tuple(packet)


def check_premises(data, rows):
    checked = 0

    def check(cdf, start, end, ratios, total):
        nonlocal checked
        if cdf[end - 1] != total or total > 1 << 41:
            raise AssertionError("wrong total/cap")
        for j, ratio in zip(range(start, end), ratios, strict=True):
            a = cdf[j] - (cdf[j - 1] if j > start else 0)
            if a < 1 or a < D * ratio:
                raise AssertionError("upward count premise failed")
            checked += 1

    for p, row in enumerate(rows):
        for c in range(len(data["pointer"]) - 1):
            start, end = data["pointer"][c : c + 2]
            mass = F(data["mass"][p][c])
            ratios = [
                upper32(row[data["members"][j]]) / mass if mass else F() for j in range(start, end)
            ]
            check(data["token"][p], start, end, ratios, data["ta"][p][c])
    outgoing, targets, pointer, labels = data["graph"]
    for e, p in enumerate(data["edge_p"]):
        mass = F(data["emass"][e])
        start, end = pointer[e : e + 2]
        check(
            data["block"],
            start,
            end,
            [F(data["mass"][p][labels[j]]) / mass if mass else F() for j in range(start, end)],
            data["ba"][e],
        )
    for s, p in enumerate(data["node_p"]):
        start, end = outgoing[s : s + 2]
        parent = F(data["scales"][p]) * F(data["h"][s])
        if not parent and any(
            F(data["emass"][e]) * F(data["h"][targets[e]]) for e in range(start, end)
        ):
            raise AssertionError("zero certified potential with positive constructed flow")
        check(
            data["edge"],
            start,
            end,
            [
                numerator / parent if parent else F()
                for numerator in (
                    F(data["emass"][e]) * F(data["h"][targets[e]]) for e in range(start, end)
                )
            ],
            data["ea"][s],
        )
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_flush_denormal(False)
    generator = np.random.default_rng(2026101651)
    cases = [
        ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
        ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
        ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
        ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
    ]
    counts = ratios_checked = proposals = completed = failures = 0
    records = []
    for case, (words, canvas, eot, pad) in enumerate(cases):
        for salt in (1, 2, 3):
            ref, law = fixture(words, canvas, eot, pad, salt=salt)
            layers = tuple(
                tuple(tuple((e.target, e.tokens) for e in node) for node in layer)
                for layer in ref.layers
            )
            sampler = TicketSampler(
                tuple((t,) for t in range(len(words))), layers, (True,), block_size=2
            )
            rows = np.asarray(ref.rows, dtype=np.float64)
            prepared = sampler.prepare(torch.from_numpy(rows).cuda())
            data = snapshot(sampler, prepared)
            counts += check_premises(data, rows)
            accepted = {}
            for word, w in law.items():
                packet = word_packet(data, word)
                q = probability(packet)
                if w / q > prepared["envelope"]:
                    raise AssertionError("GPU count envelope fails full-word maximum")
                a = acceptance(
                    [rows[p, t] for p, t in enumerate(word)], packet, prepared["envelope"]
                )
                if a != w / (prepared["envelope"] * q):
                    raise AssertionError("integer scalar correction changed law")
                accepted[word] = q * a
                ratios_checked += 1
            rate = sum(accepted.values(), F())
            if rate != ref.mass / prepared["envelope"]:
                raise AssertionError("accepted mass/rate mismatch")
            for word, w in law.items():
                if accepted[word] / rate != w / ref.mass:
                    raise AssertionError("accepted original-word law changed")
            source = generator.integers(0, 1 << 32, (64, len(canvas), 3, 2), dtype=np.int64)
            source[0] = 0
            source[1] = (1 << 32) - 1
            result = sampler.propose(prepared, torch.from_numpy(source).cuda())
            found = result["tokens"].cpu().tolist()
            packets = result["packet"].cpu().reshape(64, -1, 3).tolist()
            selected = result["weights"].cpu().tolist()
            for i, word in enumerate(found):
                expected, packet = replay(data, source[i])
                if tuple(word) != expected or tuple(map(tuple, packets[i])) != packet:
                    raise AssertionError(
                        "actual finite GPU proposal/packet differs from CPU integer law"
                    )
                if selected[i] != [rows[p, t] for p, t in enumerate(word)]:
                    raise AssertionError("selected original binary64 bits changed")
                proposals += 1
            sample = sampler.sample_prepared(
                prepared,
                16,
                Random(case * 100 + salt),
                generator=torch.Generator(device="cuda").manual_seed(case * 100 + salt),
            )
            for word, status in zip(
                sample["tokens"].cpu().tolist(), sample["statuses"], strict=True
            ):
                if status == "FAIL":
                    failures += 1
                    continue
                if law[tuple(word)] <= 0 or any(
                    t is not None and word[p] != t for p, t in enumerate(canvas)
                ):
                    raise AssertionError("accepted sample changed original target/fixed IDs")
                stop = word.index(eot)
                if any(t != pad for t in word[stop + 1 :]):
                    raise AssertionError("accepted EOT/PAD changed")
                json.loads(b"".join(words[t] for t in word[:stop]).decode("utf8"))
                completed += 1
            records.append(
                dict(
                    case=case,
                    salt=salt,
                    acceptance_lower=str(prepared["acceptance_lower"]),
                    target_words=len(law),
                )
            )
    # Nontrivial blocks/aliases and NONACCEPTING leaves: original weight alone
    # must never accept a syntactically nonaccepting proposal.
    classes = ((0, 1, 2), (3, 4, 5), (6, 7))
    layers = ((((0, (0, 1)), (1, (2,))),), (((0, (0, 1, 2)),), ((1, (0, 1, 2)),)))
    sampler = TicketSampler(classes, layers, (True, False), block_size=2)
    rows = np.array(
        [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], [0, 0.125, 0.25, 0.5, 1, 0, 0.75, 0.1]],
        dtype=np.float64,
    )
    prepared = sampler.prepare(torch.from_numpy(rows).cuda())
    data = snapshot(sampler, prepared)
    counts += check_premises(data, rows)
    law = {
        w: F(float(rows[0, w[0]])) * F(float(rows[1, w[1]])) if w[0] < 6 else F()
        for w in itertools.product(range(8), repeat=2)
    }
    accepted = {}
    for word, w in law.items():
        packet = word_packet(data, word)
        q = probability(packet)
        a = acceptance(
            [rows[p, t] for p, t in enumerate(word)],
            packet,
            prepared["envelope"],
            valid=word[0] < 6,
        )
        if w / q > prepared["envelope"] or a != w / (q * prepared["envelope"]):
            raise AssertionError("block/nonaccepting envelope or acceptance mismatch")
        accepted[word] = q * a
        ratios_checked += 1
    rate = sum(accepted.values(), F())
    total = sum(law.values(), F())
    if any(accepted[w] / rate != value / total for w, value in law.items()):
        raise AssertionError("nonaccepting leaves changed accepted law")
    source = generator.integers(0, 1 << 32, (64, 2, 3, 2), dtype=np.int64)
    source[0] = 0
    source[1] = (1 << 32) - 1
    result = sampler.propose(prepared, torch.from_numpy(source).cuda())
    nonaccepting = 0
    packets = result["packet"].cpu().reshape(64, -1, 3).tolist()
    for i, (word, valid) in enumerate(
        zip(result["tokens"].cpu().tolist(), result["valid"].cpu().tolist(), strict=True)
    ):
        expected, packet = replay(data, source[i])
        if (
            tuple(word) != expected
            or tuple(map(tuple, packets[i])) != packet
            or valid != (word[0] < 6)
        ):
            raise AssertionError("nonaccepting original-ID GPU proposal changed")
        nonaccepting += int(not valid)
        proposals += 1
    if not nonaccepting:
        raise AssertionError("must exercise a nonaccepting proposal")
    # Explicit numerical limitation: lower0 is inconclusive, not infeasibility.
    tiny = TicketSampler(((0,),), ((((0, (0,)),),),), (True,))
    tiny_weights = torch.tensor([[float.fromhex("0x1p-1074")]], dtype=torch.float64, device="cuda")
    try:
        tiny.prepare(tiny_weights)
    except ValueError as error:
        if "inconclusive" not in str(error):
            raise
    else:
        raise AssertionError("tiny positive mass must not bypass admission")
    competing = tiny.control.sample(
        tiny_weights, torch.zeros((1, 1, 3), dtype=torch.long, device="cuda"), [Random(0)]
    )
    if competing["tokens"].item() != 0 or competing["fallback_count"] != 1:
        raise AssertionError("strong interval control must retain exact tiny-mass fallback")
    payload = dict(
        status="PASS",
        count_premises=counts,
        full_word_ratios=ratios_checked,
        literal_finite_proposal_replays=proposals,
        accepted_jsons=completed,
        nonaccepting_proposals_checked=nonaccepting,
        tiny_positive_refusal_and_strong_control_fallback=True,
        finite_budget_fails=failures,
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        gpu=torch.cuda.get_device_name(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
        records=records,
    )
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("sources", "records")}))


if __name__ == "__main__":
    main()
