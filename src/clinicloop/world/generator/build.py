"""World builder for SimClinic."""

from typing import NamedTuple

import numpy as np


class World(NamedTuple):
    """Container for generated world entities.

    Attributes:
        patients: List of generated Patient entities.
        questionnaires: List of generated Questionnaire entities.
        consults: List of generated Consult entities.
        prescriptions: List of generated Prescription entities.
        orders: List of generated Order entities.
        messages: List of generated Message entities.
    """

    patients: list
    questionnaires: list
    consults: list
    prescriptions: list
    orders: list
    messages: list


def generate_world(
    seed: int,
    population_size: int,
    span_days: int,
) -> World:
    """Generate a complete SimClinic world.

    Args:
        seed: Random seed for reproducibility.
        population_size: Number of patients to generate.
        span_days: Number of days the simulation spans.

    Returns:
        A World containing all generated entities.

    Raises:
        NotImplementedError: This stub must be implemented.
    """
    raise NotImplementedError("generate_world stub")
