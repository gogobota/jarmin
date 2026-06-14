#!/bin/bash
set -euo pipefail

DOWNLOADS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/downloads"
mkdir -p "$DOWNLOADS_DIR"
cd "$DOWNLOADS_DIR"

curl -O https://www.mkgmap.org.uk/download/splitter-r654.zip
unzip -o splitter-r654.zip

curl -O https://www.mkgmap.org.uk/download/mkgmap-r4924.zip
unzip -o mkgmap-r4924.zip

curl -O http://m.m.i24.cc/osmconvert.c
gcc osmconvert.c -lz -O3 -o osmconvert

brew install osmium-tool
