#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

for script in "$ROOT"/scripts/*.sh; do
    bash -n "$script"
done

grep -q '0.0.0.0/0' "$ROOT/infra/template.yaml"
grep -q 'FromPort: 80' "$ROOT/infra/template.yaml"
grep -q 'FromPort: 22' "$ROOT/infra/template.yaml"
grep -q 'return 200 "OK' "$ROOT/infra/template.yaml"
grep -q 'aws:RequestedRegion.*ap-northeast-2' "$ROOT/iam/deployment-policy.json"
if grep -q '"AdministratorAccess"' "$ROOT/iam/deployment-policy.json"; then
    echo 'AdministratorAccess must not be granted.' >&2
    exit 1
fi

echo 'B3-1 artifact smoke test passed'
