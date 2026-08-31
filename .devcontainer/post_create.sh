#!/bin/bash
set -e



sudo apt-get update
sudo apt-get install -y default-mysql-client default-mysql-server git build-essential wget

sudo service mariadb start || echo "WARNING: mariadb service failed to start -- check manually with: sudo service mariadb status"

cd ~


wget http://www.cs.unm.edu/~mccune/mace4/download/LADR-2009-11A.tar.gz
tar xzf LADR-2009-11A.tar.gz
cd LADR-2009-11A


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
python3 -m pip install -e ~/macleod-src

# macleod reads its own config from a hardcoded path: ~/macleod/macleod_linux.conf
mkdir -p ~/macleod
cp .devcontainer/macleod_linux.conf ~/macleod/macleod_linux.conf
sed -i "s|^path:.*|path: $HOME/colore/ontologies|; s|^home:.*|home: $HOME/|" ~/macleod/macleod_linux.conf

cd /workspaces/seadoo-main
python3 -m pip install -r requirements.txt nicegui mysql-connector-python

echo "Container ready. COLORE is at ~/colore, macleod source at ~/macleod-src, macleod config at ~/macleod/macleod_linux.conf"