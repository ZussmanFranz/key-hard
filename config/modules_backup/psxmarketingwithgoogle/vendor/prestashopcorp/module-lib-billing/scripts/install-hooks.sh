#!/bin/bash
HOOKS_DIR=".git/hooks"
HOOK_FILE="pre-commit"

echo "Installing pre-commit hook..."
mkdir -p "$HOOKS_DIR"
cp ./scripts/$HOOK_FILE "$HOOKS_DIR/$HOOK_FILE"
chmod +x "$HOOKS_DIR/$HOOK_FILE"
echo "Pre-commit hook installed successfully."