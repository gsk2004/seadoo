#!/bin/bash
# test_pipeline.sh
#
# Run this INSIDE the devcontainer (Reopen in Container first), from the
# repo root. Sanity-checks the pipeline in increasing order of scope, so a
# failure tells you roughly where to look instead of failing silently 200
# hierarchies in.
set -e

echo "=== 0. Confirming COLORE and macleod are where post_create.sh put them ==="
ls ~/colore/ontologies 2>&1 | head -3 || echo "FAIL: ~/colore/ontologies not found -- did post_create.sh's COLORE clone run?"
cat ~/macleod/macleod_linux.conf > /dev/null 2>&1 || echo "FAIL: ~/macleod/macleod_linux.conf not found"

echo
echo "=== 1. Checking Prover9/Mace4 are on PATH ==="
which prover9 || { echo "FAIL: prover9 not found"; exit 1; }
which mace4 || { echo "FAIL: mace4 not found"; exit 1; }

echo
echo "=== 2. Checking MySQL/MariaDB is running ==="
sudo service mariadb status || echo "FAIL: mariadb not running -- try: sudo service mariadb start"

echo
echo "=== 3. Checking macleod is importable ==="
python3 -c "import macleod.parsing.parser; import macleod.Filemgt; print('macleod OK')" \
    || { echo "FAIL: macleod not importable -- check pip install -e ~/macleod-src ran"; exit 1; }

echo
echo "=== 4. Checking seadoo's config.py exists and is valid ==="
python3 -c "import config; print('clif_repo:', config.clif_repo)" \
    || { echo "FAIL: config.py missing or invalid -- copy config_template.py and fill it in, with clif_repo pointing at ~/colore/ontologies"; exit 1; }

echo
echo "=== 5. Dry run against the FULL COLORE checkout (no writes) ==="
python3 sync.py --clif-root ~/colore/ontologies --dry-run

echo
echo "=== 6. Real run against ONE small hierarchy only ==="
echo "    (orderings is a good first target -- small, and root_theory"
echo "     quasi_order is already referenced in db/insert.sql)"
python3 sync.py --clif-root ~/colore/ontologies/orderings \
                --manifest .manifest_orderings_test.json

echo
echo "=== 7. Spot-check the result ==="
echo "Generated .in files in orderings/:"
find ~/colore/ontologies/orderings -name "*.in" | head -5
echo
echo "Chain decomposition CSV:"
cat ~/colore/ontologies/orderings/chain_decomposition.csv 2>/dev/null \
    || echo "(none written -- check the run above for errors)"

echo
echo "=== Done. If steps 1-7 all passed, scale up: ==="
echo "  python3 sync.py --clif-root ~/colore/ontologies"
echo
echo "Then, once you're ready to index hierarchies in MySQL:"
echo "  python3 populate_hierarchies.py --colore-ontologies ~/colore/ontologies"