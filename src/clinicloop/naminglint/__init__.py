"""Naming lint module for detecting forbidden names and I6 words."""

from clinicloop.naminglint.scanner import load_denylist, scan_payload, scan_tree

__all__ = ["load_denylist", "scan_tree", "scan_payload"]
