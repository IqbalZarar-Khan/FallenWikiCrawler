#!/usr/bin/env bash
set -e
echo "==================================================="
echo "  Starting FallenWiki Crawler (Local Mode)"
echo "==================================================="
python3 -m pip install -r requirements.txt
python3 main.py
