---
name: new-spec
description: Create a new specification from template
---

Create a new specification document from the template.

Usage: /new-spec [name]

```bash
# Get the specification name from arguments or prompt
SPEC_NAME="${1:-}"
if [ -z "$SPEC_NAME" ]; then
    echo "Please provide a specification name (e.g., 'user-authentication'):"
    read SPEC_NAME
fi

# Convert to lowercase and replace spaces with hyphens
SPEC_NAME=$(echo "$SPEC_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

# Create the specification file
SPEC_FILE="specifications/${SPEC_NAME}.md"

if [ -f "$SPEC_FILE" ]; then
    echo "Error: Specification '$SPEC_FILE' already exists!"
    exit 1
fi

# Copy template
cp specifications/TEMPLATE.md "$SPEC_FILE"

# Update the title in the new file
sed -i '' "s/\[Feature\/Component Name\]/${SPEC_NAME}/" "$SPEC_FILE" 2>/dev/null || \
sed -i "s/\[Feature\/Component Name\]/${SPEC_NAME}/" "$SPEC_FILE"

echo "Created new specification: $SPEC_FILE"
echo "Opening in editor..."
```

Now open the file for editing:

```python
import os
spec_file = os.environ.get('SPEC_FILE', 'specifications/new-spec.md')
print(f"Please edit the specification at: {spec_file}")
```