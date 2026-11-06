#!/bin/sh
# Verify that artifacts/ matches the frozen golden output byte-for-byte.
#
# The goldens in tests/golden/ were produced by the Python pipeline
# (stages/run_all.py) at the commit that introduced them. They are the
# acceptance test for the Common Lisp rewrite: the port is correct when this
# script passes, and each ported stage is checked against it as it lands.
#
# Deliberately language-neutral: it must keep working after stages/ is
# deleted. Run whatever produces artifacts/ first, then run this.
#
# Usage:  sh tests/verify_golden.sh
# Exit:   0 = identical, 1 = drift (details on stdout)

set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
golden="$root/tests/golden"
artifacts="$root/artifacts"

[ -d "$artifacts" ] || { echo "FAIL: no artifacts/; run the pipeline first"; exit 1; }

status=0
checked=0

# _intermediate/ is intentionally not a golden: it is a Python-only staging
# cache that the Lisp rewrite does not reproduce (values are threaded in
# memory instead). Comparing it would fail the port for the wrong reason.
for g in "$golden"/*; do
    name=$(basename "$g")
    [ "$name" = "MANIFEST.sha256" ] && continue
    a="$artifacts/$name"
    checked=$((checked + 1))
    if [ ! -f "$a" ]; then
        echo "MISSING  $name"
        status=1
    elif ! cmp -s "$g" "$a"; then
        echo "DIFFERS  $name"
        status=1
    fi
done

# Extra artifacts are drift too: a new output file is a change to the
# deliverable and should be an explicit decision, not a silent one.
for a in "$artifacts"/*; do
    [ -f "$a" ] || continue
    name=$(basename "$a")
    [ -f "$golden/$name" ] || { echo "UNEXPECTED  $name (not in goldens)"; status=1; }
done

if [ "$status" -eq 0 ]; then
    echo "OK: $checked artifacts match goldens"
else
    echo
    echo "Artifacts drifted from tests/golden/."
    echo "If the change is intended, review the diff, then refresh with:"
    echo "  cp artifacts/*.* tests/golden/ && (cd tests/golden && shasum -a 256 *.* > MANIFEST.sha256)"
fi
exit "$status"
