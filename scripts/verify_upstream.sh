#!/usr/bin/env bash
set -euo pipefail
expected="5b1b31098f34ed3691d2a9f4aae14fdf5839d072"
expected_url="https://github.com/hyundong98/EPIC-Decoding.git"
expected_license="5b23746803b6d9687562034f4e31a8dcddeb47521517c8fcb72c7401f71a9388"
expected_third_party="f6456782c874f543c3b8ea703fa07d5fdcf2624b516b5df8f990df48f9753124"
path="vendor/EPIC-Decoding"

if [[ ! -e "$path/.git" ]]; then
  echo "EPIC submodule is not initialized. Run: git submodule update --init --recursive" >&2
  exit 1
fi

actual="$(git -C "$path" rev-parse HEAD)"
if [[ "$actual" != "$expected" ]]; then
  echo "Unexpected EPIC commit: $actual (expected $expected)" >&2
  exit 1
fi

configured_url="$(git config --file .gitmodules --get submodule.vendor/EPIC-Decoding.url)"
if [[ "$configured_url" != "$expected_url" ]]; then
  echo "Unexpected EPIC submodule URL: $configured_url (expected $expected_url)" >&2
  exit 1
fi

configured_branch="$(git config --file .gitmodules --get submodule.vendor/EPIC-Decoding.branch)"
if [[ "$configured_branch" != "main" ]]; then
  echo "Unexpected EPIC default branch: $configured_branch (expected main)" >&2
  exit 1
fi

remote_url="$(git -C "$path" remote get-url origin)"
if [[ "$remote_url" != "$expected_url" ]]; then
  echo "Unexpected EPIC origin URL: $remote_url (expected $expected_url)" >&2
  exit 1
fi

for notice in LICENSE THIRD_PARTY_LICENSES.md; do
  if [[ ! -f "$path/$notice" ]]; then
    echo "Missing upstream notice: $path/$notice" >&2
    exit 1
  fi
done

license_hash="$(sha256sum "$path/LICENSE" | cut -d' ' -f1)"
third_party_hash="$(sha256sum "$path/THIRD_PARTY_LICENSES.md" | cut -d' ' -f1)"
if [[ "$license_hash" != "$expected_license" || "$third_party_hash" != "$expected_third_party" ]]; then
  echo "Upstream license notice hash mismatch" >&2
  exit 1
fi

if [[ -n "$(git -C "$path" status --porcelain)" ]]; then
  echo "EPIC submodule has tracked or untracked changes; it must remain read-only" >&2
  exit 1
fi

echo "EPIC upstream verified at $actual"
