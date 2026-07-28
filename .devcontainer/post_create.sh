#!/bin/bash
set -e

git config --global user.name "gsk2004"

git config --global user.email "gauri.karajagi@gmail.com"

sudo apt-get update
sudo apt-get install -y default-mysql-client default-mysql-server git build-essential wget

sudo service mariadb start || echo "WARNING: mariadb service failed to start -- check manually with: sudo service mariadb status"

cd ~

# Prover9/Mace4 -- not available as apt packages on bullseye, build from source.
# `make all` fails on modern gcc/ld for two separate reasons:
#   1. gcc 10+ defaults to -fno-common, breaking this 2009-era code -- fixed
#      with CFLAGS=-fcommon.
#   2. prover9's own Makefile links `-lm` BEFORE the object files that need
#      it (round/ceil), which modern ld's strict left-to-right symbol
#      resolution can't handle -- `make all` still fails at that final link
#      step even with -fcommon, so we let it fail (|| true) and relink
#      prover9 by hand afterward with -lm moved to the end. mace4 builds and
#      links fine on its own and doesn't need this.
wget http://www.cs.unm.edu/~mccune/mace4/download/LADR-2009-11A.tar.gz
tar xzf LADR-2009-11A.tar.gz
cd LADR-2009-11A

# `make all` at the top level runs subdirectories in order: ladr -> mace4.src
# -> provers.src -> apps.src, and stops the whole recipe the instant any one
# of them fails (no -k flag). provers.src ALWAYS fails here (see below), which
# means apps.src -- and everything after it -- never gets built by this call.
# `|| true` only stops the script itself from exiting; it does NOT make `make`
# continue past the failure. So provers.src and apps.src both need to be
# built explicitly afterward, standalone.
make all CFLAGS=-fcommon || true


cd provers.src
gcc -fcommon -o prover9 prover9.o index_lits.o forward_subsume.o demodulate.o \
    pred_elim.o unfold.o semantics.o giv_select.o white_black.o actions.o \
    search.o utilities.o provers.o foffer.o ../ladr/libladr.a -lm
cd ..


cd apps.src && make all CFLAGS=-fcommon && cd ..


sudo cp bin/mace4 /usr/local/bin/
sudo cp provers.src/prover9 /usr/local/bin/
sudo cp bin/interpformat bin/prooftrans /usr/local/bin/

cd ~ && rm -rf LADR-2009-11A*

which prover9 && which mace4 && which interpformat && which prooftrans   # fail loudly here if anything is missing

# COLORE and macleod's SOURCE
git clone https://github.com/gruninger/colore.git ~/colore
git clone https://github.com/thahmann/macleod.git ~/macleod-src
pip install -e ~/macleod-src

# macleod reads its own config from a hardcoded path: ~/macleod/macleod_linux.conf
mkdir -p ~/macleod
cp /workspaces/seadoo-main/.devcontainer/macleod_linux.conf ~/macleod/macleod_linux.conf

cd /workspaces/seadoo-main
pip install -r requirements.txt nicegui mysql-connector-python

echo "Container ready. COLORE is at ~/colore, macleod source at ~/macleod-src, macleod config at ~/macleod/macleod_linux.conf"