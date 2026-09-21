"""Process control scripts for enforcing development discipline rules.

This module provides scripts that verify and enforce process rules:
- tdd_check: Verifies that commits follow test-first discipline
- dispatch: Prevents parallel work on overlapping file ownership
- post_merge_sync: Verifies local state after merge
"""
