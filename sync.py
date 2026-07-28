"""
sync.py

Orchestrates the full pipeline:
  1. Walk config.clif_repo for .clif files, hash each one, diff against a
     stored manifest to find new / changed / removed files since last run.
  2. For new/changed files: translate .clif -> .in via p9_tools.clif_pipeline
     (which imports macleod directly -- this is the actual translation step).
  3. For each hierarchy (subdirectory of clif_repo) touched by a new/changed
     file: insert the newly translated theory into that hierarchy's chain
     decomposition CSV via p9_tools.insertion.insertion.
  4. For removed files: report them for manual review. Deliberately NOT
     automated -- removing a node from the poset can require re-linking
     theories that pointed to it, which is unsafe to do unattended.
  5. Write the updated manifest back to disk.

Assumes each hierarchy is a subdirectory directly under config.clif_repo,
containing both .clif sources and their generated .in files side by side,
plus a chain-decomposition CSV named CSV_NAME (default: chain_decomposition.csv).
Adjust CSV_NAME below if your existing CSVs use a different naming convention.
"""

import argparse
import hashlib
import importlib
import json
import logging
import os

import config
import p9_tools.clif_pipeline as clif_pipeline

LOGGER = logging.getLogger(__name__)

CSV_NAME = "chain_decomposition.csv"


def compute_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_clif_files(root):
    """Return {relpath: abspath} for every .clif file under root."""
    found = {}
    for directory, _subdirs, files in os.walk(root):
        for fname in files:
            if fname.endswith(clif_pipeline.CLIF_ENDING):
                abspath = os.path.join(directory, fname)
                relpath = os.path.relpath(abspath, root)
                found[relpath] = abspath
    return found


def load_manifest(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_manifest(path, manifest):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def expected_in_path(relpath, clif_root):
    """Where clif_to_prover9 would have written this file's .in output."""
    hierarchy_dir = hierarchy_dir_for(relpath, clif_root)
    base_name = os.path.splitext(os.path.basename(relpath))[0]
    return os.path.join(hierarchy_dir, base_name + clif_pipeline.P9_ENDING)


def diff_manifest(old_manifest, current_files, clif_root):
    """
    :return: (new_relpaths, changed_relpaths, removed_relpaths, current_hashes)

    A file counts as "changed" (needs retranslation) not only when its hash
    differs from the manifest, but also when its hash matches yet its
    expected .in output is missing on disk. This handles the case where the
    destination directory (e.g. ~/colore, which is NOT part of the persisted
    /workspaces bind mount) gets wiped and re-cloned fresh -- the .clif
    source files come back byte-identical (same hash), but every previously
    generated .in file and chain_decomposition.csv is gone. Without this
    check, sync.py would see "hash unchanged" and silently skip retranslating
    everything, even though none of the outputs actually exist anymore.
    """
    new_files = []
    changed_files = []
    current_hashes = {}

    for relpath, abspath in current_files.items():
        current_hash = compute_hash(abspath)
        current_hashes[relpath] = current_hash

        if relpath not in old_manifest:
            new_files.append(relpath)
        elif old_manifest[relpath] != current_hash:
            changed_files.append(relpath)
        elif not os.path.exists(expected_in_path(relpath, clif_root)):
            LOGGER.warning(
                "%s hash unchanged but expected output %s is missing -- "
                "retranslating (destination directory likely got wiped, "
                "e.g. a container rebuild that re-cloned ~/colore fresh)",
                relpath, expected_in_path(relpath, clif_root))
            changed_files.append(relpath)

    removed_files = [r for r in old_manifest if r not in current_files]

    return new_files, changed_files, removed_files, current_hashes


def hierarchy_dir_for(relpath, clif_root):
    """The top-level subdirectory a .clif file lives under, e.g. 'orderings'."""
    parts = relpath.split(os.sep)
    return os.path.join(clif_root, parts[0]) if len(parts) > 1 else clif_root


def insert_into_hierarchy(hierarchy_dir, theory_names):
    """
    Insert each newly translated theory (by .in filename, no directory) into
    the chain decomposition CSV for hierarchy_dir, one at a time, using
    seadoo's existing p9_tools.insertion.insertion module.
    """
    csv_path = os.path.join(hierarchy_dir, CSV_NAME)

    if not os.path.exists(csv_path):
        # bootstrap: first theory in a brand-new hierarchy becomes chain 0
        if not theory_names:
            return
        first, rest = theory_names[0], theory_names[1:]
        with open(csv_path, "w") as f:
            f.write("0\n{}\n".format(first.replace(".in", "")))
        LOGGER.info("Bootstrapped new hierarchy CSV at %s with %s", csv_path, first)
        theory_names = rest

    if not theory_names:
        return

    # config.hierarchy / config.csv / config.function are read as
    # module-level constants when p9_tools.insertion.insertion is imported --
    # and p9_tools.relationship.relationship reads config.hierarchy the same
    # way (as FILE_PATH). Both must be reloaded on every hierarchy, not just
    # insertion: a plain `import` inside insertion.py won't re-execute
    # relationship.py's module-level code since Python caches imports, so
    # without reloading it explicitly here, relationship.FILE_PATH would stay
    # frozen at whichever hierarchy happened to be processed first in this
    # run, and every hierarchy after that would silently look for theory
    # files in the wrong directory.
    config.hierarchy = hierarchy_dir
    config.csv = csv_path
    config.function = 1

    import p9_tools.relationship.relationship as relationship
    importlib.reload(relationship)
    import p9_tools.insertion.insertion as insertion
    importlib.reload(insertion)

    for name in theory_names:
        LOGGER.info("Inserting %s into %s", name, csv_path)
        insertion.main(new_t=name, hierarchy=True)


def run(clif_root, manifest_path, dry_run=False):
    current_files = discover_clif_files(clif_root)
    old_manifest = load_manifest(manifest_path)

    new_files, changed_files, removed_files, current_hashes = diff_manifest(
        old_manifest, current_files, clif_root)

    print("New: {}, Changed: {}, Removed: {}".format(
        len(new_files), len(changed_files), len(removed_files)))

    if removed_files:
        print("\nThe following .clif files were removed from the source repo.")
        print("Poset removal is NOT automated -- review these by hand:")
        for r in removed_files:
            print("  ", r)

    if dry_run:
        print("\nDry run -- no translation or insertion performed.")
        return

    # translate every new/changed file, and track which theories (by bare
    # .in filename) landed in which hierarchy directory, in the order they
    # were translated. Each entry also carries its source relpath, so an
    # insertion failure downstream can exclude it from the manifest too.
    to_insert = {}   # hierarchy_dir -> [(theory .in filename, source relpath)]
    translation_failures = []
    failed_relpaths = set()

    for relpath in new_files + changed_files:
        clif_path = current_files[relpath]
        hierarchy_dir = hierarchy_dir_for(relpath, clif_root)

        try:
            # resolve=True: many COLORE theories assert no axioms of their
            # own and are built entirely from cl-imports of other modules
            # (e.g. disconnected_semilinear.clif). Without resolving those
            # imports, such theories translate to an EMPTY .in file, which
            # both misrepresents the theory's actual content and crashes
            # p9_tools.insertion/relationship (they don't handle a
            # zero-axiom theory -- see the IndexError on lines[0]).
            in_path = clif_pipeline.clif_to_prover9(clif_path, dest_dir=hierarchy_dir, resolve=True)
        except Exception as exc:
            LOGGER.error("Translation failed for %s: %s", clif_path, exc)
            translation_failures.append((clif_path, str(exc)))
            failed_relpaths.add(relpath)
            continue

        # even with resolve=True, a handful of COLORE files are genuinely
        # content-free (pure index/bundle files, e.g. orderings_def.clif).
        # These aren't meaningful nodes in an interpretability hierarchy --
        # skip them explicitly rather than handing insertion.py an empty
        # theory it isn't built to handle.
        axiom_count = clif_pipeline._count_in_axioms(in_path)
        if axiom_count == 0:
            LOGGER.warning("Skipping %s -- translated to 0 axioms, not inserting into any poset", in_path)
            continue

        to_insert.setdefault(hierarchy_dir, []).append((os.path.basename(in_path), relpath))

    insertion_failures = []
    for hierarchy_dir, entries in to_insert.items():
        theory_names = [name for name, _relpath in entries]
        try:
            insert_into_hierarchy(hierarchy_dir, theory_names)
        except Exception as exc:
            LOGGER.error("Insertion failed for hierarchy %s (theories: %s): %s",
                         hierarchy_dir, theory_names, exc)
            insertion_failures.append((hierarchy_dir, theory_names, str(exc)))
            # don't mark any of this hierarchy's source files as done -- the
            # CSV write may not have completed, so these need to be retried
            # rather than silently considered synced next run.
            for _name, relpath in entries:
                failed_relpaths.add(relpath)

    if insertion_failures:
        print("\n{} hierarchy/hierarchies FAILED insertion -- chain_decomposition.csv "
              "for these may be missing, empty, or stale (whatever it looked like "
              "before this run). Their source .clif files were excluded from the "
              "manifest and will be retried next run:".format(len(insertion_failures)))
        for hierarchy_dir, theory_names, msg in insertion_failures:
            print("  {} (theories: {}): {}".format(hierarchy_dir, theory_names, msg))

    if translation_failures:
        print("\n{} file(s) FAILED translation -- not inserted into any poset:".format(
            len(translation_failures)))
        for clif_path, msg in translation_failures:
            print("  {}: {}".format(clif_path, msg))

    # drop removed files from the manifest, and record success for anything
    # that translated cleanly. Anything in failed_relpaths is deliberately
    # left OUT of the manifest so it gets retried on the next run instead
    # of being silently marked "done" despite having failed.
    for relpath in removed_files:
        old_manifest.pop(relpath, None)
    for relpath in new_files + changed_files:
        if relpath in failed_relpaths:
            old_manifest.pop(relpath, None)
            continue
        old_manifest[relpath] = current_hashes[relpath]

    save_manifest(manifest_path, old_manifest)
    print("\nManifest updated at", manifest_path)


def main():
    parser = argparse.ArgumentParser(description="Sync COLORE .clif sources into SEADOO .in files and poset hierarchies.")
    parser.add_argument("--clif-root", type=str, default=config.clif_repo)
    parser.add_argument("--manifest", type=str, default=os.path.join(config.path, "manifest.json"))
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    run(args.clif_root, args.manifest, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
    