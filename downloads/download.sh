#!/bin/bash

curl -O https://www.mkgmap.org.uk/download/splitter-r654.zip
unzip -f splitter-r654.zip

curl -O https://www.mkgmap.org.uk/download/mkgmap-r4924.zip
unzip -f mkgmap-r4924.zip

curl -O http://m.m.i24.cc/osmconvert.c
gcc osmconvert.c -lz -O3 -o osmconvert
