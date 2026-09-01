#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 artifact-rebuild|source-experiment-rerun" >&2
  exit 2
fi
mode=$1
case "$mode" in
  artifact-rebuild|source-experiment-rerun) ;;
  *)
    echo "usage: $0 artifact-rebuild|source-experiment-rerun" >&2
    exit 2
    ;;
esac

for required_command in git python3.11 diff sha256sum; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "missing required command: $required_command" >&2
    exit 2
  fi
done

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(git -C "$script_directory" rev-parse --show-toplevel)
host_python="$repository_root/.venv/bin/python"
host_maturin="$repository_root/.venv/bin/maturin"

if [ ! -x "$host_python" ]; then
  echo "missing host build environment: run make bootstrap first" >&2
  exit 2
fi
if [ "$mode" = "source-experiment-rerun" ] && [ ! -x "$host_maturin" ]; then
  echo "missing maturin in host build environment: run make bootstrap first" >&2
  exit 2
fi
if [ -n "$(git -C "$repository_root" status --porcelain --untracked-files=normal)" ]; then
  echo "CPU rehearsal requires a clean source worktree" >&2
  exit 2
fi

rehearsal_root=$(mktemp -d "/tmp/mwpc-cpu-rehearsal.XXXXXX")
cleanup() {
  if [ -d "$rehearsal_root" ]; then
    find "$rehearsal_root" -depth -delete
  fi
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

checkout="$rehearsal_root/checkout"
wheelhouse="$rehearsal_root/wheelhouse"
environment="$rehearsal_root/wheel-environment"
outside_checkout="$rehearsal_root/outside-checkout"
mkdir -p "$wheelhouse" "$outside_checkout"

git clone --quiet --no-hardlinks "$repository_root" "$checkout"
git -C "$checkout" submodule update --init --recursive
"$host_python" -m build \
  --no-isolation \
  --wheel \
  --outdir "$wheelhouse" \
  "$checkout"

main_wheel_count=$(find "$wheelhouse" -maxdepth 1 -type f -name 'mwpc_exact-*.whl' | wc -l)
if [ "$main_wheel_count" -ne 1 ]; then
  echo "expected exactly one mwpc-exact wheel" >&2
  exit 2
fi
main_wheel=$(find "$wheelhouse" -maxdepth 1 -type f -name 'mwpc_exact-*.whl')

python3.11 -m venv "$environment"
environment_python="$environment/bin/python"
"$environment_python" -m pip install --no-index --no-deps "$main_wheel"
(
  cd "$outside_checkout"
  "$environment_python" -I -c \
    'import json, sys; from pathlib import Path; import mwpc_exact, mwpc_research; checkout=Path(sys.argv[1]).resolve(); paths={m.__name__: str(Path(m.__file__).resolve()) for m in (mwpc_exact, mwpc_research)}; assert all(not Path(path).is_relative_to(checkout) for path in paths.values()); print(json.dumps(paths, sort_keys=True))' \
    "$checkout"
)

source_commit=$(git -C "$checkout" rev-parse HEAD)

if [ "$mode" = "artifact-rebuild" ]; then
  reference="$rehearsal_root/reference"
  processed_relative="docs/artifacts/processed/t1203_final_results_v1"
  paper_relative="paper/generated/t1203_final_results_v1"
  config="$checkout/configs/analysis/t1203_final_artifacts_v1.toml"
  mkdir -p \
    "$reference/docs/artifacts/processed" \
    "$reference/paper/generated"
  mv "$checkout/$processed_relative" "$reference/docs/artifacts/processed/"
  mv "$checkout/$paper_relative" "$reference/paper/generated/"

  "$environment_python" -I \
    "$checkout/scripts/exact_commit/build_final_artifacts.py" \
    --config "$config"
  diff --recursive --no-dereference \
    "$reference/$processed_relative" \
    "$checkout/$processed_relative"
  diff --recursive --no-dereference \
    "$reference/$paper_relative" \
    "$checkout/$paper_relative"
  "$environment_python" -I \
    "$checkout/scripts/exact_commit/build_final_artifacts.py" \
    --config "$config" \
    --verify-existing

  manifest="$checkout/$processed_relative/artifact-manifest.json"
  printf '%s\n' \
    "REHEARSAL_LEVEL=artifact-rebuild" \
    "ARTIFACT_REBUILD=PASS" \
    "source_commit=$source_commit" \
    "wheel=$(basename "$main_wheel")" \
    "byte_comparison=all_processed_and_paper_outputs" \
    "manifest_sha256=$(sha256sum "$manifest" | cut -d ' ' -f 1)"
  exit 0
fi

binding_wheelhouse="$rehearsal_root/binding-wheelhouse"
mkdir -p "$binding_wheelhouse"
PYO3_PYTHON="$environment_python" "$host_maturin" build \
  --release \
  --manifest-path "$checkout/crates/mwpc_parser_py/Cargo.toml" \
  --out "$binding_wheelhouse"
binding_wheel_count=$(find "$binding_wheelhouse" -maxdepth 1 -type f -name 'mwpc_parser_py-*.whl' | wc -l)
if [ "$binding_wheel_count" -ne 1 ]; then
  echo "expected exactly one mwpc-parser-py wheel" >&2
  exit 2
fi
binding_wheel=$(find "$binding_wheelhouse" -maxdepth 1 -type f -name 'mwpc_parser_py-*.whl')
"$environment_python" -m pip install --no-index --no-deps "$binding_wheel"
"$environment_python" -I -c \
  'from pathlib import Path; import mwpc_parser_py; print(Path(mwpc_parser_py.__file__).resolve())'

source_root="$rehearsal_root/source-experiment-rerun"
raw_directory="$source_root/raw"
processed_directory="$source_root/processed"
semantic_summary="$source_root/semantic-summary.json"
rehearsal_table="$source_root/correctness-rerun-table.tex"
reference_rows="$checkout/docs/artifacts/raw/t1203_final_results_v1/q1-correctness-cases.jsonl"
candidate_rows="$raw_directory/q1-cases.jsonl"

"$environment_python" -I \
  "$checkout/scripts/exact_commit/run_q1_correctness.py" \
  --config "$checkout/configs/experiments/q1_correctness_v1.toml" \
  --run-directory "$raw_directory" \
  --processed-directory "$processed_directory"
"$environment_python" -I -m mwpc_research.correctness_rehearsal \
  --reference "$reference_rows" \
  --candidate "$candidate_rows" \
  --summary-output "$semantic_summary" \
  --table-output "$rehearsal_table"

printf '%s\n' \
  "REHEARSAL_LEVEL=source-experiment-rerun" \
  "SOURCE_EXPERIMENT_RERUN=PASS" \
  "source_commit=$source_commit" \
  "wheel=$(basename "$main_wheel")" \
  "raw_rows_sha256=$(sha256sum "$candidate_rows" | cut -d ' ' -f 1)" \
  "semantic_summary_sha256=$(sha256sum "$semantic_summary" | cut -d ' ' -f 1)" \
  "table_sha256=$(sha256sum "$rehearsal_table" | cut -d ' ' -f 1)" \
  "timing_fields_compared=false"
