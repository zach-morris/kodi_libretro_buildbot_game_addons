#!/bin/bash
# Replace the last build commit with the new add-ons. GitHub rejects pushes
# over 2 GB, so each changed folder is first uploaded on a temporary branch,
# which leaves only a small push to move the build branch.
set -euo pipefail

message=$1
branch=$(git rev-parse --abbrev-ref HEAD)
upload=build-upload

git config user.name "GitHub Actions Bot"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git add -A
if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi
dirs=$(git diff --cached --name-only | sed -n 's|/.*||p' | sort -u)
git reset -q

base=$(git rev-parse HEAD)
for dir in $dirs; do
  git add -A -- "$dir"
  git commit -q -m "$message ($dir)"
  git push -f origin "HEAD:refs/heads/$upload"
done

git add -A
git reset -q --soft "$base"
git commit -q --amend -m "$message" --author="$GITHUB_ACTOR <$GITHUB_ACTOR@users.noreply.github.com>"
git push -f origin "HEAD:$branch"
if [ -n "$dirs" ]; then
  git push -q origin --delete "$upload"
fi
