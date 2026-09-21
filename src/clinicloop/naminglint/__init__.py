"""Naming lint module for detecting forbidden names and I6 words."""

from clinicloop.naminglint.scanner import load_denylist, scan_payload, scan_tree

__all__ = ["load_denylist", "scan_tree", "scan_payload"]

# CLI entry points can be imported directly:
# from clinicloop.naminglint.lint import main as lint_main
# from clinicloop.naminglint.hash_names import main as hash_names_main
