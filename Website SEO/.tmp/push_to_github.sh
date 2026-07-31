#!/bin/bash
# Push index-new.html to GitHub and enable Pages

TOKEN="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"
REPO_NAME="apl-preview"
SRC="/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/en/index-new.html"
TMPDIR_REPO="/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/.tmp/apl-preview"

echo "=== Step 1: Get GitHub username ==="
USERNAME=$(curl -s -H "Authorization: token $TOKEN" -H "User-Agent: bash" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
echo "Username: $USERNAME"

if [ -z "$USERNAME" ]; then
  echo "ERROR: Could not get username. Token may be invalid."
  exit 1
fi

echo ""
echo "=== Step 2: Delete existing repo if present ==="
curl -s -X DELETE \
  -H "Authorization: token $TOKEN" \
  -H "User-Agent: bash" \
  "https://api.github.com/repos/$USERNAME/$REPO_NAME" 
echo "Delete attempted (ignore 404 if not found)"

echo ""
echo "=== Step 3: Create new public repo ==="
REPO_RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "User-Agent: bash" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$REPO_NAME\",\"description\":\"AI Profit Lab Homepage Preview\",\"private\":false,\"auto_init\":true}" \
  "https://api.github.com/user/repos")
echo "$REPO_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Repo URL:', d.get('html_url','ERROR'))"

echo ""
echo "=== Step 4: Initialize local git repo ==="
cd "$TMPDIR_REPO"
rm -f placeholder.txt

# Copy the HTML as index.html
cp "$SRC" index.html
echo "Copied index-new.html -> index.html"

# Copy the image assets and favicon
cp "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/nahid-aby.jpg" .
cp "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/nahid-aby-about.jpg" .
cp "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/favicon.svg" .
echo "Copied assets: nahid-aby.jpg, nahid-aby-about.jpg, favicon.svg"

# Modify paths to load relatively for GitHub Pages
sed -i '' 's|\.\./nahid-aby\.jpg|./nahid-aby.jpg|g' index.html
sed -i '' 's|\.\./nahid-aby-about\.jpg|./nahid-aby-about.jpg|g' index.html
sed -i '' 's|/favicon\.svg|./favicon.svg|g' index.html
echo "Patched relative asset paths in index.html"

rm -rf .git
git init -b main 2>/dev/null || git init && git checkout -b main 2>/dev/null || true
git config user.email "ai.profit.lab2026@gmail.com"
git config user.name "AI Profit Lab"
git add index.html nahid-aby.jpg nahid-aby-about.jpg favicon.svg
git commit -m "Add homepage preview with assets"

echo ""
echo "=== Step 5: Push to GitHub ==="
REMOTE="https://$USERNAME:$TOKEN@github.com/$USERNAME/$REPO_NAME.git"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# Wait a moment for GitHub to finish repo init
sleep 3

git push -f origin main 2>&1

echo ""
echo "=== Step 6: Enable GitHub Pages ==="
sleep 2
PAGES_RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "User-Agent: bash" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  -d '{"source":{"branch":"main","path":"/"}}' \
  "https://api.github.com/repos/$USERNAME/$REPO_NAME/pages")
echo "$PAGES_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Pages URL:', d.get('html_url','check output'))"

echo ""
echo "================================================"
echo "DONE!"
echo "GitHub Repo:   https://github.com/$USERNAME/$REPO_NAME"
echo "Live Preview:  https://$USERNAME.github.io/$REPO_NAME/"
echo "(GitHub Pages takes 1-3 minutes to go live)"
echo "================================================"
