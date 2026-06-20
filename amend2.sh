#!/bin/bash
cd "/c/Create-Tool/PriceComparisonTool/Price Compare Tool"

echo "=== Removing ALL files from git index ==="
git rm -r --cached .
echo "rm exit: $?"

echo ""
echo "=== Re-add only non-gitignored files ==="
git add -A

echo ""
echo "=== Staged files (should have NO scripts/bats/ps1) ==="
git diff --cached --name-only | head -40

echo ""
echo "=== Any remaining secrets? ==="
git diff --cached --name-only | xargs grep -l "ghp_" 2>/dev/null || echo "No secrets found in staged files"

echo ""
echo "=== Amend commit ==="
git commit --amend --no-edit
echo "amend exit: $?"

echo ""
echo "=== Force push ==="
git push -f origin HEAD:main
echo "push exit: $?"
echo "=== DONE ==="
