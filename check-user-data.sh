#!/bin/bash
# Script to check Signal data location

echo "=== Signal Development Data Location Check ==="
echo ""
echo "Current user: $(whoami)"
echo "Home directory: $HOME"
echo ""

# Determine OS and expected path
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    EXPECTED_PATH="$HOME/.config/Signal-development"
    PROD_PATH="$HOME/.config/Signal"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    EXPECTED_PATH="$HOME/Library/Application Support/Signal-development"
    PROD_PATH="$HOME/Library/Application Support/Signal"
else
    EXPECTED_PATH="$APPDATA/Signal-development"
    PROD_PATH="$APPDATA/Signal"
fi

echo "Expected development data path: $EXPECTED_PATH"
echo "Production data path: $PROD_PATH"
echo ""

# Check if directories exist
if [ -d "$EXPECTED_PATH" ]; then
    echo "✓ Development directory exists"
    if [ -f "$EXPECTED_PATH/sql/db.sqlite" ]; then
        echo "✓ Database file exists"
        DB_SIZE=$(du -sh "$EXPECTED_PATH/sql/db.sqlite" 2>/dev/null | cut -f1)
        echo "  Database size: $DB_SIZE"
    else
        echo "✗ Database file NOT found"
    fi

    if [ -d "$EXPECTED_PATH/attachments.noindex" ]; then
        ATTACH_COUNT=$(find "$EXPECTED_PATH/attachments.noindex" -type f 2>/dev/null | wc -l)
        echo "✓ Attachments directory exists ($ATTACH_COUNT files)"
    else
        echo "✗ Attachments directory NOT found"
    fi
else
    echo "✗ Development directory does NOT exist"
    echo ""
    echo "To fix this:"
    if [ -d "$PROD_PATH" ]; then
        echo "✓ Production Signal directory found"
        echo "Run this command to copy your production data:"
        echo "  cp -r \"$PROD_PATH\" \"$EXPECTED_PATH\""
    else
        echo "✗ Production Signal directory NOT found at $PROD_PATH"
        echo "Make sure Signal Desktop is installed and you've used it before."
    fi
fi

echo ""
echo "=== End Check ==="
