#!/bin/sh
set -eu
output="$(mktemp)"
trap 'rm -f "$output"' EXIT
if kubectl run forbidden-root -n jobboard --image=busybox:1.37 --restart=Never --dry-run=server -- sleep 60 >"$output" 2>&1; then
  cat "$output"; echo "FAIL: charge non conforme acceptée"; exit 1
fi
cat "$output"
if grep -q 'violates PodSecurity' "$output"; then
  echo "PASS: charge rejetée par Pod Security Admission."
else
  echo "INCONCLUSIF: échec sans preuve de rejet PodSecurity."; exit 1
fi
