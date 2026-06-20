#!/bin/bash
cd "/c/Create-Tool/PriceComparisonTool/Price Compare Tool"

echo "=== Unstaging secret-containing files ==="
git rm --cached push.sh fix.sh d.sh d2.sh d3.sh b.sh 2>/dev/null
git rm --cached redeploy.ps1 2>/dev/null
git rm --cached "git-push.bat" "git-push.ps1" "build_frontend.bat" "open-pricecart.bat" 2>/dev/null
git rm -r --cached push_fix.py push_fix2.py push_fix3.py 2>/dev/null
git rm --cached find_blinkit_api.py 2>/dev/null

echo ""
echo "=== Re-staging with updated .gitignore ==="
git add -A

echo ""
echo "=== Status (should not show script files) ==="
git status --short | grep -v "^?" | head -30

echo ""
echo "=== Amending commit ==="
git commit --amend --no-edit
echo "amend exit: $?"

echo ""
echo "=== Force pushing ==="
git push -f origin HEAD:main
echo "push exit: $?"
echo "=== DONE ==="
