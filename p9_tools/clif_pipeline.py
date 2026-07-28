"""
clif_pipeline.py



"""

import argparse
import logging
import os
import re
import shutil

import macleod.Filemgt as Filemgt
import macleod.parsing.parser as Parser

LOGGER = logging.getLogger(__name__)

CLIF_ENDING = Filemgt.read_config('cl', 'ending')          # '.clif'
P9_ENDING = '.in'                                          # seadoo's convention


_INVALID_QUOTED_CONSTANT = re.compile(r"'([A-Za-z_][A-Za-z0-9_]*)'")


def _strip_invalid_quoted_constants(in_path):
    """Rewrite a generated .in file in place, stripping macleod's invalid
    single-quoting around bare-identifier constants. Returns the number of
    substitutions made, so callers can log/verify."""
    with open(in_path, "r") as f:
        content = f.read()

    fixed_content, count = _INVALID_QUOTED_CONSTANT.subn(r"\1", content)

    if count:
        with open(in_path, "w") as f:
            f.write(fixed_content)

    return count


def _macleod_basepath():
    """macleod's (sub, base) pair used to resolve cl-imports URIs to paths."""
    sub, base = Filemgt.get_ontology_basepath()
    return sub, base


def _count_in_axioms(in_path):
    """Count axiom lines actually written to a generated .in file."""
    count = 0
    with open(in_path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("%"):
                continue
            if stripped.startswith("formulas(") or stripped.startswith("end_of_list"):
                continue
            count += 1
    return count


def clif_to_prover9(clif_path, dest_dir=None, resolve=False, verify=True):
    """
    Translate a single .clif file to a SEADOO-style .in Prover9 file.

    :return: path to the generated .in file
    """
    sub, base = _macleod_basepath()

    ontology = Parser.parse_file(clif_path, sub, base, resolve,
                                  preserve_conditionals=True)

    if ontology is None:
        raise ValueError("macleod failed to parse: {}".format(clif_path))

    if resolve:
        ontology.resolve_imports()

    parsed_axiom_count = len(ontology.get_all_axioms())
    p9_path = ontology.write_ladr_file()

    if dest_dir is None:
        dest_dir = os.path.dirname(os.path.abspath(clif_path))
    os.makedirs(dest_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(clif_path))[0]
    final_path = os.path.join(dest_dir, base_name + P9_ENDING)
    shutil.copyfile(p9_path, final_path)

    quoted_fixes = _strip_invalid_quoted_constants(final_path)
    if quoted_fixes:
        LOGGER.info("Stripped %d invalid quoted-constant reference(s) in %s",
                    quoted_fixes, final_path)

    if verify:
        written_count = _count_in_axioms(final_path)
        if written_count != parsed_axiom_count:
            raise ValueError(
                "Axiom count mismatch for {}: macleod parsed {} axiom(s) from "
                "the .clif file but {} ended up in {}. Do not trust this "
                "translation -- inspect both files by hand before using it."
                .format(clif_path, parsed_axiom_count, written_count, final_path))
        LOGGER.info("Verified %s: %d axioms in, %d axioms out",
                    clif_path, parsed_axiom_count, written_count)

    LOGGER.info("Translated %s -> %s", clif_path, final_path)
    return final_path


def translate_tree(source_root, dest_root=None, resolve=False, verify=True):
    """
    Walk source_root for .clif files and translate each into a .in file.

    :return: (generated, failed)
    """
    generated = []
    failed = []

    for directory, _subdirs, files in os.walk(source_root):
        for fname in files:
            if not fname.endswith(CLIF_ENDING):
                continue

            clif_path = os.path.join(directory, fname)

            if dest_root is None:
                dest_dir = directory
            else:
                rel = os.path.relpath(directory, source_root)
                dest_dir = os.path.join(dest_root, rel) if rel != '.' else dest_root

            try:
                out_path = clif_to_prover9(clif_path, dest_dir=dest_dir,
                                            resolve=resolve, verify=verify)
                generated.append(out_path)
            except Exception as exc:
                LOGGER.error("Failed to translate %s: %s", clif_path, exc)
                failed.append((clif_path, str(exc)))

    return generated, failed


def main():
    parser = argparse.ArgumentParser(
        description='Translate CLIF (.clif) files into Prover9 (.in) files for use with SEADOO.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', type=str, help='Path to a single .clif file')
    group.add_argument('--folder', type=str, help='Path to a folder to search recursively for .clif files')

    parser.add_argument('--out', type=str, default=None)
    parser.add_argument('--resolve', action='store_true', default=False)
    parser.add_argument('--no-verify', action='store_true', default=False)

    args = parser.parse_args()
    verify = not args.no_verify

    if args.file:
        out_path = clif_to_prover9(args.file, dest_dir=args.out, resolve=args.resolve, verify=verify)
        print("Wrote:", out_path)
    else:
        out_paths, failures = translate_tree(args.folder, dest_root=args.out,
                                              resolve=args.resolve, verify=verify)
        print("Wrote {} file(s):".format(len(out_paths)))
        for p in out_paths:
            print(" ", p)
        if failures:
            print("\n{} file(s) FAILED translation or verification:".format(len(failures)))
            for clif_path, msg in failures:
                print("  {}: {}".format(clif_path, msg))


if __name__ == '__main__':
    main()