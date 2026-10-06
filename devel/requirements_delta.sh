#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

report() {
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        tee -a "$GITHUB_STEP_SUMMARY"
    else
        cat
    fi
}

if [ ! -f /requirements.txt ]; then
    echo "The running image ships no /requirements.txt, so it predates the baked dependency list and there is nothing to compare requirements.txt against. Expected until the image carrying that file is published (dodona-edu/docker-images#483, plus a publish run)." | report
    exit 1
fi

# Requirement lines only: comments legitimately differ on either side.
requirement_lines() { grep -Ev '^[[:space:]]*(#|$)' "$1" | sort; }

requirement_lines requirements.txt > /tmp/repo-requirements.txt
requirement_lines /requirements.txt > /tmp/image-requirements.txt

if diff -u --label 'image /requirements.txt' --label 'requirements.txt' /tmp/image-requirements.txt /tmp/repo-requirements.txt > /tmp/requirements.diff; then
    echo "requirements.txt matches the dependency list the image ships." | report
    exit 0
fi

{
    echo "requirements.txt does not match the dependency list the image ships. Either this branch proposes a dependency change the image has not shipped yet, in which case the PR becomes mergeable once docker-images has published it; or main's requirements.txt went stale after a publish, in which case merging the Dependabot sync PR closes the gap."
    echo
    echo '```diff'
    cat /tmp/requirements.diff
    echo '```'
} | report

exit 1
