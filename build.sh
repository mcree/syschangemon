#!/bin/bash
set -e
DEST=$(dirname $0)/build
echo "building syschangemon in $DEST"
mkdir -p "$DEST"
rm -rf "$DEST"/*
pip3 install --target "$DEST" -r "$DEST"/../requirements.txt
cp -r "$DEST"/../syschangemon "$DEST"
cat <<EOF >"$DEST"/run.py
#!/usr/bin/python3
import sys
sys.path.insert(0,'.')
import syschangemon.cli.main
syschangemon.cli.main.main()
EOF
chmod +x "$DEST"/run.py
