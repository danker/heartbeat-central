---
name: ship
description: Run lint, test, commit all changes, and push to GitHub
---

Run quality checks, tests, then commit and push if everything passes.

```bash
echo "🚀 Starting ship process..."
echo

# Step 1: Run lint
./scripts/lint.sh
if [ $? -ne 0 ]; then
    echo "❌ Linting failed. Please fix the issues and try again."
    exit 1
fi
echo

# Step 2: Run tests
./scripts/test.sh
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Please fix the failing tests and try again."
    exit 1
fi
echo

# Step 3: Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "📭 No changes to commit."
    exit 0
fi

# Step 4: Show changes
echo "📋 Changes to be committed:"
git status --short
echo

# Step 5: Generate commit message based on changes
echo "💬 Generating commit message..."

# Analyze changes to create a meaningful commit message
MODIFIED_FILES=$(git diff --name-only --cached 2>/dev/null | wc -l | tr -d ' ')
NEW_FILES=$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')
TOTAL_CHANGES=$((MODIFIED_FILES + NEW_FILES))

# Build commit message based on changes
if [ "$NEW_FILES" -gt 0 ] && [ "$MODIFIED_FILES" -gt 0 ]; then
    COMMIT_MSG="feat: add new features and update existing files"
elif [ "$NEW_FILES" -gt 0 ]; then
    # List the main new additions
    NEW_DIRS=$(git ls-files --others --exclude-standard | cut -d'/' -f1 | sort -u | head -3 | tr '\n' ', ' | sed 's/,$//')
    COMMIT_MSG="feat: add ${NEW_DIRS}"
elif [ "$MODIFIED_FILES" -gt 0 ]; then
    # List the main modified files
    MODIFIED=$(git diff --name-only | head -3 | xargs basename -a | tr '\n' ', ' | sed 's/,$//')
    COMMIT_MSG="update: modify ${MODIFIED}"
else
    COMMIT_MSG="chore: update project files"
fi

# Add file count to message
COMMIT_MSG="${COMMIT_MSG} (${TOTAL_CHANGES} files)"

echo "📝 Commit message: ${COMMIT_MSG}"
echo

# Step 6: Commit all changes
echo "📦 Committing changes..."
git add -A
git commit -m "$COMMIT_MSG"
if [ $? -ne 0 ]; then
    echo "❌ Commit failed."
    exit 1
fi
echo "✅ Changes committed!"
echo

# Step 7: Push to remote
echo "🔄 Pushing to remote..."
git push
if [ $? -ne 0 ]; then
    echo "❌ Push failed. You may need to pull first or resolve conflicts."
    exit 1
fi

echo "✅ Successfully shipped! 🎉"
```