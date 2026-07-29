#!/usr/bin/env python3
"""
audit_coverage.py

Compares, for every hierarchy in the COLORE checkout, how many .clif files
exist versus how many distinct theories actually made it into that
hierarchy's chain_decomposition.csv. Read-only -- makes no changes.

Usage:
    python3 audit_coverage.py --colore-ontologies ~/colore/ontologies

Output: a table sorted by the biggest gaps first (most missing theories),
so you can see at a glance whether cases like hyfo_flow are common or rare,
and a summary count of hierarchies with no gap / some gap / no CSV at all.
"""

import argparse
import csv
import os


def count_clif_files(hierarchy_dir):
    return len([f for f in os.listdir(hierarchy_dir)
                if f.endswith(".clif") and os.path.isfile(os.path.join(hierarchy_dir, f))])


def count_chain_theories(hierarchy_dir):
    csv_path = os.path.join(hierarchy_dir, "chain_decomposition.csv")
    if not os.path.exists(csv_path):
        return None
    theories = set()
    with open(csv_path, "r") as f:
        rows = list(csv.reader(f))
    for row in rows[1:]: # skip header row
        for cell in row:
            if cell.strip():
                theories.add(cell.strip())
    return len(theories)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--colore-ontologies", type=str, required=True)
    args = parser.parse_args()

    root = os.path.expanduser(args.colore_ontologies)
    results = []

    for name in sorted(os.listdir(root)):
        hierarchy_dir = os.path.join(root, name)
        if not os.path.isdir(hierarchy_dir):
            continue
        clif_count = count_clif_files(hierarchy_dir)
        if clif_count == 0:
            continue
        chain_count = count_chain_theories(hierarchy_dir)
        results.append((name, clif_count, chain_count))

    no_csv = [r for r in results if r[2] is None]
    with_gap = [r for r in results if r[2] is not None and r[2] < r[1]]
    clean = [r for r in results if r[2] is not None and r[2] >= r[1]]

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Total hierarchies with .clif files: {}".format(len(results)))
    print(" No chain_decomposition.csv yet: {}".format(len(no_csv)))
    print(" CSV exists but missing theories: {}".format(len(with_gap)))
    print(" CSV theory count >= .clif count: {}".format(len(clean)))
    print()

    if with_gap:
        print("=" * 70)
        print("HIERARCHIES WITH MISSING THEORIES (biggest gap first)")
        print("=" * 70)
        print("{:<40} {:>10} {:>10} {:>8}".format("hierarchy", ".clif files", "in chain", "missing"))
        for name, clif_count, chain_count in sorted(with_gap, key=lambda r: r[1] - r[2], reverse=True):
            print("{:<40} {:>10} {:>10} {:>8}".format(name, clif_count, chain_count, clif_count - chain_count))
        print()

    if no_csv:
        print("=" * 70)
        print("HIERARCHIES WITH NO chain_decomposition.csv AT ALL")
        print("=" * 70)
        for name, clif_count, _ in sorted(no_csv, key=lambda r: r[1], reverse=True):
            print("{:<40} {:>10} .clif files".format(name, clif_count))


if __name__ == "__main__":
    main()