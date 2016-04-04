#!/bin/bash
set -e
DEST=$(dirname $0)/build
echo "building syschangemon in $DEST"
mkdir -p "$DEST"
rm -rf "$DEST"/*

# build /usr/share/syschangemon
mkdir -p "$DEST"
pip3 install --target "$DEST" -r "$DEST"/../requirements.txt
cp -r "$DEST"/../syschangemon "$DEST"
cp "$DEST"/../bin/* "$DEST"
chmod +x "$DEST"/run.sh
chmod +x "$DEST"/run.py
