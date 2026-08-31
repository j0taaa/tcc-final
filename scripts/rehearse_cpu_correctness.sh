#!/usr/bin/env bash
set -euo pipefail

for required_command in git make python3.11 cmp sha256sum; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "missing required command: $required_command" >&2
    exit 2
  fi
done

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(git -C "$script_directory" rev-parse --show-toplevel)

if [ -n "$(git -C "$repository_root" status --porcelain --untracked-files=normal)" ]; then
  echo "CPU rehearsal requires a clean source worktree" >&2
  exit 2
fi

rehearsal_root=$(mktemp -d "${TMPDIR:-/tmp}/mwpc-cpu-rehearsal.XXXXXX")
cleanup() {
  if [ -d "$rehearsal_root" ]; then
    find "$rehearsal_root" -depth -delete
  fi
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

checkout="$rehearsal_root/checkout"
reference="$rehearsal_root/reference"
processed_relative="docs/artifacts/processed/t1203_final_results_v1"
paper_relative="paper/generated/t1203_final_results_v1"
correctness_relative="$paper_relative/correctness-oracle-table.tex"

git clone --quiet --no-hardlinks "$repository_root" "$checkout"
git -C "$checkout" submodule update --init --recursive
make -C "$checkout" bootstrap

mkdir -p "$reference/docs/artifacts/processed" "$reference/paper/generated"
mv "$checkout/$processed_relative" "$reference/docs/artifacts/processed/"
mv "$checkout/$paper_relative" "$reference/paper/generated/"

make -C "$checkout" final-artifacts
cmp \
  "$reference/$correctness_relative" \
  "$checkout/$correctness_relative"
make -C "$checkout" final-artifacts-check

correctness_sha256=$(sha256sum "$checkout/$correctness_relative" | cut -d ' ' -f 1)
printf '%s\n' \
  "T1204_CPU_REHEARSAL=PASS" \
  "source_commit=$(git -C "$checkout" rev-parse HEAD)" \
  "artifact=$correctness_relative" \
  "sha256=$correctness_sha256"
