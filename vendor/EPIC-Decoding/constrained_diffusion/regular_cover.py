from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable, Sequence

from rustformlang.cfg import CFG
from rustformlang.fa.epsilon_nfa import ENFA, epsilon, minimize_enfa_threaded

from constrained_diffusion import fast_enfa_profiler as enfa_prof
from constrained_diffusion.constrain_utils import (
    EOS,
    generated_language,
    is_intersection_empty_for_generated_language,
    dfa_free_checker_enabled,
)


def regular_cover_batch_enabled() -> bool:
    return os.environ.get("CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH", "0") == "1"


def regular_cover_exact_enabled() -> bool:
    return os.environ.get("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "1") != "0"


def regular_cover_min_batch() -> int:
    return int(os.environ.get("CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH", "2"))


@dataclass(frozen=True)
class BatchCandidate:
    index: int
    token_id: int
    word: object  # str or EOS
    score: float = 0.0

_EPSILON_STRINGS = {"", "epsilon", "ε", "ϵ", "eps", "EPS", "Epsilon"}
_ARROW_RE = re.compile(r"\s*(.*?)\s*(?:->|→|::=)\s*(.*)\s*$")


def _split_alternatives(rhs: str) -> list[str]:
    parts: list[list[str]] = [[]]
    for tok in rhs.split():
        if tok == "|":
            parts.append([])
        else:
            parts[-1].append(tok)
    return [" ".join(p) for p in parts]


def _parse_cfg_text(text: str) -> tuple[str, list[tuple[str, tuple[str, ...]]]]:
    productions: list[tuple[str, tuple[str, ...]]] = []
    pending_lhs: str | None = None
    start: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("|") and pending_lhs is not None:
            lhs = pending_lhs
            rhs_text = line[1:].strip()
        else:
            m = _ARROW_RE.match(line)
            if not m:
                continue
            lhs = m.group(1).strip()
            rhs_text = m.group(2).strip()
            pending_lhs = lhs
            if start is None:
                start = lhs
        for alt in _split_alternatives(rhs_text):
            toks = tuple(tok for tok in alt.split() if tok not in _EPSILON_STRINGS)
            productions.append((lhs, toks))
    if start is None:
        raise ValueError("Could not parse CFG text: no productions found")
    lhs_set = {lhs for lhs, _ in productions}
    if "S" in lhs_set:
        start = "S"
    return start, productions


@lru_cache(maxsize=64)
def _build_flat_rtn_cover_dfa_from_text(cfg_text: str):
    start, productions = _parse_cfg_text(cfg_text)
    nonterminals = {lhs for lhs, _ in productions}
    by_lhs: dict[str, list[tuple[str, ...]]] = {}
    for lhs, rhs in productions:
        by_lhs.setdefault(lhs, []).append(rhs)

    enfa = ENFA()
    eps = epsilon()
    transitions: list[tuple[str, str, str]] = []

    def entry(nt: str) -> str:
        return f"N::{nt}::entry"

    def exit(nt: str) -> str:
        return f"N::{nt}::exit"

    prod_id = 0
    for lhs, rhss in by_lhs.items():
        for rhs in rhss:
            pid = prod_id
            prod_id += 1
            transitions.append((entry(lhs), eps, f"P::{pid}::0"))
            transitions.append((f"P::{pid}::{len(rhs)}", eps, exit(lhs)))
            for i, sym in enumerate(rhs):
                src = f"P::{pid}::{i}"
                dst = f"P::{pid}::{i+1}"
                if sym in nonterminals:
                    transitions.append((src, eps, entry(sym)))
                    transitions.append((exit(sym), eps, dst))
                else:
                    transitions.append((src, sym, dst))
    enfa.set_start_state(entry(start))
    enfa.add_accept_state(exit(start))
    if hasattr(enfa, "add_transitions"):
        enfa.add_transitions(transitions)
    else:
        for tr in transitions:
            enfa.add_transition(*tr)
    return minimize_enfa_threaded(enfa)


def get_flat_rtn_cover_dfa(cfg: CFG):
    return _build_flat_rtn_cover_dfa_from_text(cfg.to_text())


def _with_candidates(words: Sequence[object], candidates: Sequence[BatchCandidate]) -> list[object]:
    out = list(words)
    for c in candidates:
        out[c.index] = c.word
    return out


def cover_allows_words(
    *,
    words_full: Sequence[object],
    prompt_len: int,
    cfg: CFG,
    lex_map,
    terminals: list[str],
    prelex: str | None,
    single_token_lexing,
    inject_gap_size: int,
    max_total_injections: int,
    subtokens,
    supertokens,
    strip_chars: str | None,
    trace: bool = False,
) -> bool:
    with enfa_prof.timer("regular_cover.generated_language"):
        lang = generated_language(
            list(words_full)[prompt_len:],
            lex_map,
            terminals,
            prelex=prelex,
            single_token_lexing=single_token_lexing,
            inject_gap_size=inject_gap_size,
            max_total_injections=max_total_injections,
            subtokens=subtokens,
            supertokens=supertokens,
            strip_chars=strip_chars,
            trace=False,
            return_graph=False,
        )
    with enfa_prof.timer("regular_cover.intersection"):
        cover = get_flat_rtn_cover_dfa(cfg)
        empty = cover.intersection(lang).is_empty()
    if trace:
        print(f"[regular-cover] cover∩partial empty={empty}")
    return not empty


def exact_allows_words(
    *,
    words_full: Sequence[object],
    prompt_len: int,
    cfg: CFG,
    lex_map,
    terminals: list[str],
    prelex: str | None,
    single_token_lexing,
    inject_gap_size: int,
    max_total_injections: int,
    subtokens,
    supertokens,
    strip_chars: str | None,
    trace: bool = False,
    timeout: float = 100,
) -> bool:
    generated_lang = generated_language(
        list(words_full)[prompt_len:],
        lex_map,
        terminals,
        prelex=prelex,
        single_token_lexing=single_token_lexing,
        inject_gap_size=inject_gap_size,
        max_total_injections=max_total_injections,
        subtokens=subtokens,
        supertokens=supertokens,
        strip_chars=strip_chars,
        trace=False,
        return_graph=dfa_free_checker_enabled(),
    )
    enfa_prof.count("regular_cover.exact.calls")
    empty = is_intersection_empty_for_generated_language(cfg, generated_lang, timeout)
    if trace:
        print(f"[regular-cover] exact CFG∩partial empty={empty}")
    return not empty


def select_batch_with_regular_cover(
    *,
    words_full: Sequence[object],
    candidates: Sequence[BatchCandidate],
    prompt_len: int,
    cfg: CFG,
    lex_map,
    terminals: list[str],
    prelex: str | None,
    single_token_lexing,
    inject_gap_size: int,
    max_total_injections: int,
    subtokens,
    supertokens,
    strip_chars: str | None,
    trace: bool = False,
) -> list[BatchCandidate]:
    if not candidates:
        return []
    ordered = sorted(candidates, key=lambda c: c.score, reverse=True)

    def cover_ok(subset: Sequence[BatchCandidate]) -> bool:
        if not subset:
            return False
        trial = _with_candidates(words_full, subset)
        return cover_allows_words(
            words_full=trial,
            prompt_len=prompt_len,
            cfg=cfg,
            lex_map=lex_map,
            terminals=terminals,
            prelex=prelex,
            single_token_lexing=single_token_lexing,
            inject_gap_size=inject_gap_size,
            max_total_injections=max_total_injections,
            subtokens=subtokens,
            supertokens=supertokens,
            strip_chars=strip_chars,
            trace=trace,
        )

    def cover_select(subset: list[BatchCandidate]) -> list[BatchCandidate]:
        if not subset:
            return []
        if cover_ok(subset):
            return subset
        if len(subset) == 1:
            return []
        mid = (len(subset) + 1) // 2
        left = cover_select(subset[:mid])
        # Use the selected left subset as part of the base when checking right.
        if left:
            base_plus_left = _with_candidates(words_full, left)
        else:
            base_plus_left = words_full
        right = select_batch_with_regular_cover(
            words_full=base_plus_left,
            candidates=subset[mid:],
            prompt_len=prompt_len,
            cfg=cfg,
            lex_map=lex_map,
            terminals=terminals,
            prelex=prelex,
            single_token_lexing=single_token_lexing,
            inject_gap_size=inject_gap_size,
            max_total_injections=max_total_injections,
            subtokens=subtokens,
            supertokens=supertokens,
            strip_chars=strip_chars,
            trace=trace,
        )
        return left + right

    selected = cover_select(ordered)
    if not selected:
        enfa_prof.count("regular_cover.batch.no_selection")
        return []

    if regular_cover_exact_enabled():
        # Shrink until an exact-CFG-compatible subset is found.
        def exact_shrink(subset: list[BatchCandidate]) -> list[BatchCandidate]:
            if not subset:
                return []
            trial = _with_candidates(words_full, subset)
            if exact_allows_words(
                words_full=trial,
                prompt_len=prompt_len,
                cfg=cfg,
                lex_map=lex_map,
                terminals=terminals,
                prelex=prelex,
                single_token_lexing=single_token_lexing,
                inject_gap_size=inject_gap_size,
                max_total_injections=max_total_injections,
                subtokens=subtokens,
                supertokens=supertokens,
                strip_chars=strip_chars,
                trace=trace,
            ):
                return subset
            if len(subset) == 1:
                return []
            mid = (len(subset) + 1) // 2
            left = exact_shrink(subset[:mid])
            if left:
                base_plus_left = _with_candidates(words_full, left)
            else:
                base_plus_left = words_full
            right = select_batch_with_regular_cover(
                words_full=base_plus_left,
                candidates=subset[mid:],
                prompt_len=prompt_len,
                cfg=cfg,
                lex_map=lex_map,
                terminals=terminals,
                prelex=prelex,
                single_token_lexing=single_token_lexing,
                inject_gap_size=inject_gap_size,
                max_total_injections=max_total_injections,
                subtokens=subtokens,
                supertokens=supertokens,
                strip_chars=strip_chars,
                trace=trace,
            )
            return left + right

        selected = exact_shrink(selected)

    if trace:
        print(
            "[regular-cover] selected batch:",
            [(c.index, c.word if c.word is not EOS else "<EOS>", c.score) for c in selected],
        )
    enfa_prof.value("regular_cover.batch.selected_size", len(selected))
    return selected
