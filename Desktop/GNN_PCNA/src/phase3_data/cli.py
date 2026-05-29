"""Command-line entrypoints for governed Phase 3 data preparation."""

from __future__ import annotations

import argparse
from pathlib import Path

from phase3_data.audit import build_residue_audit_manifest, index_manifest
from phase3_data.cif_archive import inspect_cif_inputs, verify_or_extract_cifs
from phase3_data.errors import Phase3DataError
from phase3_data.io import write_json
from phase3_data.manifests import validate_governed_inputs
from phase3_data.models import Phase3Paths
from phase3_data.provenance import command_from_argv, utc_timestamp


def _paths(args: argparse.Namespace) -> Phase3Paths:
    return Phase3Paths(root=Path(args.root))


def _timestamp_slug() -> str:
    return utc_timestamp().replace(":", "").replace("-", "").replace("+", "_").replace("T", "_")


def _default_registry_path(root: Path, stem: str) -> Path:
    return root / "data" / "registries" / f"{stem}_{_timestamp_slug()}.json"


def cmd_validate_inputs(args: argparse.Namespace) -> int:
    paths = _paths(args)
    manifest = validate_governed_inputs(paths)
    manifest["cif_inputs"] = inspect_cif_inputs(paths)
    output = Path(args.output) if args.output else None
    if output:
        digest = write_json(output, manifest)
        print(f"Wrote validation manifest: {output} ({digest})")
    else:
        print(manifest)
    return 0


def cmd_verify_or_extract_cifs(args: argparse.Namespace) -> int:
    paths = _paths(args)
    manifest = verify_or_extract_cifs(paths, command_from_argv())
    output = Path(args.output) if args.output else _default_registry_path(
        paths.root, "phase3_cif_extraction_manifest"
    )
    digest = write_json(output, manifest)
    print(f"Wrote CIF extraction manifest: {output} ({digest})")
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    paths = _paths(args)
    manifest = index_manifest(
        paths,
        command=command_from_argv(),
        requested_split=args.split,
        validation_fold=args.validation_fold,
    )
    output = Path(args.output) if args.output else _default_registry_path(
        paths.root, "phase3_dataset_index"
    )
    digest = write_json(output, manifest)
    print(f"Wrote dataset index: {output} ({digest})")
    return 0


def cmd_audit_residues(args: argparse.Namespace) -> int:
    paths = _paths(args)
    manifest = build_residue_audit_manifest(
        paths,
        command=command_from_argv(),
        requested_split=args.split,
        validation_fold=args.validation_fold,
        limit=args.limit,
    )
    output = Path(args.output) if args.output else _default_registry_path(
        paths.root, "phase3_residue_audit_manifest"
    )
    digest = write_json(output, manifest)
    print(f"Wrote residue audit manifest: {output} ({digest})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root containing data/, src/, reports/.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-inputs")
    validate.add_argument("--output")
    validate.set_defaults(func=cmd_validate_inputs)

    extract = subparsers.add_parser("verify-or-extract-cifs")
    extract.add_argument("--output")
    extract.set_defaults(func=cmd_verify_or_extract_cifs)

    build_index = subparsers.add_parser("build-index")
    build_index.add_argument("--split", choices=["all", "train", "validation", "test"], default="all")
    build_index.add_argument("--validation-fold", choices=["train-0", "train-1", "train-2", "train-3"])
    build_index.add_argument("--output")
    build_index.set_defaults(func=cmd_build_index)

    audit = subparsers.add_parser("audit-residues")
    audit.add_argument("--split", choices=["all", "train", "validation", "test"], default="all")
    audit.add_argument("--validation-fold", choices=["train-0", "train-1", "train-2", "train-3"])
    audit.add_argument("--limit", type=int)
    audit.add_argument("--output")
    audit.set_defaults(func=cmd_audit_residues)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Phase3DataError as exc:
        parser.exit(2, f"Phase 3 data error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

