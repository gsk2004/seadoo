"""
populate_hierarchies.py

Populates the `hierarchies` MySQL table (db/create.sql) from the COLORE
checkout and any chain-decomposition CSVs sync.py has generated so far.

IMPORTANT: this table only stores per-hierarchy METADATA (see db/create.sql):
  hierarchy_name, nondecomp_hierarchies, num_prim_relations, relation_name,
  root_theory
It does NOT store the actual theorem/chain ordering -- that stays in the
per-hierarchy chain_decomposition.csv files sync.py maintains. Don't confuse
the two: this script is populating a lightweight index of hierarchies, not
migrating the poset itself into the database.
"""

import argparse
import csv
import os

import config
from db import create_schema

CSV_NAME = "chain_decomposition.csv"


def find_hierarchies(colore_ontologies_root):
    """Each subdirectory under ontologies/ is one hierarchy."""
    return sorted(
        d for d in os.listdir(colore_ontologies_root)
        if os.path.isdir(os.path.join(colore_ontologies_root, d))
    )


def root_theory_for(hierarchy_dir):
    """First theory listed in this hierarchy's chain CSV, if one exists yet."""
    csv_path = os.path.join(hierarchy_dir, CSV_NAME)
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 2:
        return None
    first_data_row = rows[1]
    return first_data_row[0] if first_data_row else None


def upsert_hierarchy(cursor, hierarchy_name, root_theory):
    cursor.execute(
        """
        INSERT INTO hierarchies (hierarchy_name, nondecomp_hierarchies,
                                  num_prim_relations, relation_name, root_theory)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE root_theory = VALUES(root_theory)
        """,
        (hierarchy_name, "", 0, "", root_theory or ""),
    )


def run(colore_ontologies_root, clif_repo):
    conn = create_schema.connect()
    if conn is None:
        print("Could not connect to MySQL -- check config.py's db settings.")
        return

    cursor = conn.cursor()
    hierarchies = find_hierarchies(colore_ontologies_root)
    print("Found {} hierarchies under {}".format(len(hierarchies), colore_ontologies_root))

    for name in hierarchies:
        hierarchy_dir = os.path.join(clif_repo, name)
        root_theory = root_theory_for(hierarchy_dir)
        upsert_hierarchy(cursor, name, root_theory)
        status = root_theory if root_theory else "no chain CSV yet -- run sync.py first"
        print("  {}: root_theory={}".format(name, status))

    conn.commit()
    cursor.close()
    conn.close()
    print("\nDone. num_prim_relations, relation_name, and nondecomp_hierarchies")
    print("still need manual review -- see db/insert.sql for hand-curated examples.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--colore-ontologies", type=str,
                         default=config.clif_repo)
    parser.add_argument("--clif-repo", type=str, default=config.clif_repo)
    args = parser.parse_args()
    run(args.colore_ontologies, args.clif_repo)

if __name__ == "__main__":
    main()