---
name: list-specs
description: List all specification documents
---

View all specification documents in the project.

```bash
echo "=== Specification Documents ==="
echo

# Check if specifications directory exists
if [ ! -d "specifications" ]; then
    echo "No specifications directory found."
    exit 0
fi

# Count specifications (excluding template and README)
SPEC_COUNT=$(find specifications -name "*.md" -not -name "TEMPLATE.md" -not -name "README.md" | wc -l | tr -d ' ')

if [ "$SPEC_COUNT" -eq 0 ]; then
    echo "No specifications found yet."
    echo "Use '/new-spec [name]' to create your first specification."
else
    echo "Found $SPEC_COUNT specification(s):"
    echo

    # List all specifications with their titles
    for spec in specifications/*.md; do
        if [[ "$spec" != *"TEMPLATE.md" ]] && [[ "$spec" != *"README.md" ]]; then
            # Extract the first heading from the file
            TITLE=$(grep -m 1 "^# " "$spec" | sed 's/^# //')
            FILENAME=$(basename "$spec")
            echo "- $FILENAME: $TITLE"
        fi
    done
fi

echo
echo "Template available at: specifications/TEMPLATE.md"
echo "README available at: specifications/README.md"
```