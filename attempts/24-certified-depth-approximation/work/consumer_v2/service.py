"""CPU-only complete-operation service for the frozen actual neural pilot."""

import argparse
import json
import resource
import signal
import sys
import traceback
from pathlib import Path

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..table import LexerTable
from .benchmark import WORK, alarm, elapsed, now, operation
from .block_stats import Partition
from .compact import load


def run_timed(call, seconds):
    """Timer cancellation belongs to the boundary; a late alarm cannot commit."""
    start = now()
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        try:
            response = call()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    except (CompilationLimit, MemoryError, TimeoutError, RecursionError) as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        response = dict(
            status="resource_refusal",
            reason=type(error).__name__ + ": " + str(error),
            operation=elapsed(start),
        )
    except Exception as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        response = dict(
            status="error",
            reason=str(error),
            traceback=traceback.format_exc(),
            operation=elapsed(start),
        )
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True)
    parser.add_argument("--vocabulary", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((WORK / "consumer-v2-neural-protocol.json").read_text())
    if args.method not in protocol["methods"]:
        raise ValueError("method not in frozen pilot")
    limit = protocol["resources"]["cpu_service_address_space_bytes"]
    resource.setrlimit(resource.RLIMIT_AS, (limit,) * 2)
    start = now()
    table = LexerTable(
        CompositionalByteLevelAdapter.from_token_pieces(json.loads(args.vocabulary.read_text()))
    )
    partition = Partition(tuple(table.class_of), len(table.classes), 1024)
    compact = args.method in ("exact_local", "exact_bidir_local", "exact_eps_local")
    modules, origin = load() if compact else (None, None)
    print(
        json.dumps(dict(status="ready", startup=elapsed(start), frozen_compiler=origin)), flush=True
    )
    method = "handoff" if args.method.startswith("handoff_") else args.method
    outside = "full_sparse" if args.method == "handoff_full_sparse" else "cursor"
    boundary = "python_dense" if args.method == "handoff_dense" else "numpy"
    signal.signal(signal.SIGALRM, alarm)
    for line in sys.stdin:
        request = json.loads(line)
        response = run_timed(
            lambda request=request: operation(
                table,
                partition,
                Path(request["case_path"]),
                method,
                outside,
                boundary,
                request["seed"],
                protocol,
                compact_modules=modules,
            ),
            protocol["resources"]["seconds"],
        )
        response["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
