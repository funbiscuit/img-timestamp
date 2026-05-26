#!/bin/bash -e

set -e

DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
cd "$DIR"

FIX=false
[[ "$1" == "--fix" ]] && FIX=true

if $FIX; then
    echo "Checking and fixing formatting..."
    .venv/bin/ruff format src

    echo "Checking and fixing with linter..."
    .venv/bin/ruff check --fix src
else
    echo "Type checking (mypy)..."
    .venv/bin/mypy src

    echo "Checking formatting..."
    .venv/bin/ruff format --check src

    echo "Checking with linter..."
    .venv/bin/ruff check src
fi
