#!/usr/bin/env bash
rc=0
test -s rolling/menu.yaml && grep -q 'maxUnavailable' rolling/menu.yaml && echo "- ✅ rolling/menu.yaml sets the strategy" || { echo "- ❌ rolling/menu.yaml has no strategy yet"; rc=1; }
ls bluegreen/*.yaml >/dev/null 2>&1 && echo "- ✅ bluegreen/ has manifests" || { echo "- ❌ bluegreen/ has no manifests yet"; rc=1; }
ls canary/*.yaml >/dev/null 2>&1 && echo "- ✅ canary/ has manifests" || { echo "- ❌ canary/ has no manifests yet"; rc=1; }
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
