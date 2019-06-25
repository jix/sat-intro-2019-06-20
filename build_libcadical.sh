#!/bin/bash

set -xeuo pipefail

[ -f cadical-rel-1.0.0.tar.gz ] ||
wget -c https://github.com/arminbiere/cadical/archive/rel-1.0.0.tar.gz \
    -O cadical-rel-1.0.0.tar.gz

[ -d cadical-rel-1.0.0 ] ||
tar xzf cadical-rel-1.0.0.tar.gz

cd cadical-rel-1.0.0

if ! [ -f makefile ]; then
    ./configure CXXFLAGS="-fPIC"
    sed -e 's/\bmake\b/$(MAKE)/' -i makefile
fi

make -j$(nproc)

${CXX:-g++} \
    -shared \
    -o ../libcadical.so \
    -Wl,--whole-archive build/libcadical.a -Wl,--no-whole-archive
