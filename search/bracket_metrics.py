"""
search/bracket_metrics.py

For a given hierarchy, computes two metrics comparing "examples only" vs
"examples + counterexamples":
  1. Number of chains that produce a bracket at all (i.e. NOT [None, None])
  2. Bracket size (strong - weak) for each chain that does produce one

Calls find_bracket() directly, NOT the full hashemi() wrapper -- this
deliberately bypasses the interactive y/n refinement loop inside hashemi(),
since that step is meant for narrowing to a single best-matching theory for
a human, not for producing a clean, reproducible numeric metric. find_bracket()
itself has no interactive component: it's a pure function of the example/
counterexample files present and returns [weak, strong] as raw chain-index
positions.

Usage:
    python3 search/bracket_metrics.py --hier orderings
"""

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import config
from search.hashemi import (
    REPO_PATH, EX_PATH, CEX_PATH, find_bracket, get_input_chains,
)
from p9_tools.parse import model


def compute_metrics(hier, use_counterexamples):
    """
    :param hier: hierarchy name, e.g. 'orderings'
    :param use_counterexamples: if False, temporarily ignores every file in
        CEX_PATH (by not letting find_bracket see any), simulating an
        "examples only" run without needing to physically move files around.
    :return: dict with 'chains_with_bracket', 'total_chains', and
        'bracket_sizes' (list of strong-weak for each chain that had one)
    """
    input_chains = get_input_chains(hier)

    chains_with_bracket = 0
    bracket_sizes = []

    # find_bracket() internally lists CEX_PATH itself -- to cleanly get an
    # "examples only" condition without touching your actual counterexample
    # files, monkey-patch os.listdir just for this call so it sees an empty
    # counterexamples directory. Cleaner than moving files around by hand
    # and guaranteed not to affect anything else.
    import search.hashemi as hashemi_module
    real_listdir = os.listdir

    def patched_listdir(path):
        if not use_counterexamples and os.path.abspath(path) == os.path.abspath(CEX_PATH):
            return []
        return real_listdir(path)

    os.listdir = patched_listdir
    try:
        for chain in input_chains:
            weak, strong = find_bracket(hier, chain)
            if weak is not None and strong is not None:
                chains_with_bracket += 1
                bracket_sizes.append(strong - weak)
    finally:
        os.listdir = real_listdir

    return {
        "total_chains": len(input_chains),
        "chains_with_bracket": chains_with_bracket,
        "bracket_sizes": bracket_sizes,
    }


def summarize(label, metrics):
    sizes = metrics["bracket_sizes"]
    print("=== {} ===".format(label))
    print("Chains with a bracket: {} / {}".format(
        metrics["chains_with_bracket"], metrics["total_chains"]))
    if sizes:
        print("Bracket sizes: min={}, max={}, mean={:.2f}".format(
            min(sizes), max(sizes), sum(sizes) / len(sizes)))
        print("Raw sizes:", sizes)
    else:
        print("No chains produced a bracket.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hier", type=str, required=True)
    args = parser.parse_args()

    config.hierarchy = args.hier

    examples_only = compute_metrics(args.hier, use_counterexamples=False)
    summarize("Examples only", examples_only)

    with_counter = compute_metrics(args.hier, use_counterexamples=True)
    summarize("Examples + counterexamples", with_counter)