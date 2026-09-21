"""World builder for SimClinic."""

from typing import NamedTuple

import numpy as np

from ..entities import Consult, Message, Order, Patient, Prescription, Questionnaire
from .fictional_ranges import (
    EMAIL_DOMAIN_FICTIONAL,
    HEALTH_ID_FICTIONAL_RANGE,
    HEALTH_ID_PREFIX_FICTIONAL,
    PHONE_AREA_CODE_FICTIONAL,
    PHONE_AREA_CODE_FICTIONAL_RANGE,
)


class World(NamedTuple):
    """Container for generated world entities.

    Attributes:
        patients: List of generated Patient entities.
        questionnaires: List of generated Questionnaire entities.
        consults: List of generated Consult entities.
        prescriptions: List of generated Prescription entities.
        orders: List of generated Order entities.
        messages: List of generated Message entities.
        seed: The seed used to generate this world.
        population_size: The population size.
        span_days: The number of days the world spans.
    """

    patients: list[Patient]
    questionnaires: list[Questionnaire]
    consults: list[Consult]
    prescriptions: list[Prescription]
    orders: list[Order]
    messages: list[Message]
    seed: int
    population_size: int
    span_days: int


def generate_world(
    seed: int,
    population_size: int,
    span_days: int,
) -> World:
    """Generate a complete SimClinic world.

    Generates a deterministic world using separate numpy.random.Generator
    streams for each entity type to ensure stream isolation.

    Args:
        seed: Random seed for reproducibility.
        population_size: Number of patients to generate.
        span_days: Number of days the simulation spans.

    Returns:
        A World containing all generated entities.
    """
    # Create a base RNG seeded with the provided seed
    base_rng = np.random.Generator(np.random.PCG64(seed))

    # Create separate streams for each entity type by using
    # spawned generators with independent SeedSequences.
    # This ensures that consuming from one stream doesn't affect others.
    seed_seq = np.random.SeedSequence(seed)
    child_seeds = seed_seq.spawn(6)

    patient_rng = np.random.Generator(np.random.PCG64(child_seeds[0]))
    questionnaire_rng = np.random.Generator(np.random.PCG64(child_seeds[1]))
    consult_rng = np.random.Generator(np.random.PCG64(child_seeds[2]))
    prescription_rng = np.random.Generator(np.random.PCG64(child_seeds[3]))
    order_rng = np.random.Generator(np.random.PCG64(child_seeds[4]))
    message_rng = np.random.Generator(np.random.PCG64(child_seeds[5]))

    # Generate entities
    patients = []
    for i in range(population_size):
        # Generate phone number from fictional range
        phone_suffix = patient_rng.integers(0, 10000000)
        phone_number = f"{PHONE_AREA_CODE_FICTIONAL}{phone_suffix:07d}"

        # Generate email domain (fictional)
        email_domain = EMAIL_DOMAIN_FICTIONAL

        # Generate health identifier from fictional range
        health_id_number = patient_rng.integers(min(HEALTH_ID_FICTIONAL_RANGE), max(HEALTH_ID_FICTIONAL_RANGE))
        health_identifier = f"{HEALTH_ID_PREFIX_FICTIONAL}{health_id_number:08d}"

        patient = Patient(
            synthetic=True,
            phone_number=phone_number,
            email_domain=email_domain,
            health_identifier=health_identifier,
        )
        patients.append(patient)

    questionnaires = [
        Questionnaire(synthetic=True)
        for _ in range(population_size)
    ]

    consults = [
        Consult(synthetic=True)
        for _ in range(population_size)
    ]

    prescriptions = [
        Prescription(synthetic=True)
        for _ in range(int(population_size * 0.3))  # ~30% get prescriptions
    ]

    orders = [
        Order(synthetic=True)
        for _ in range(int(population_size * 0.2))  # ~20% have orders
    ]

    # Generate messages - these should not be seeded from the patient count
    # This tests stream isolation (AC6)
    message_count = int(population_size * 0.5)  # ~50% activity level
    messages = [
        Message(synthetic=True)
        for _ in range(message_count)
    ]

    return World(
        patients=patients,
        questionnaires=questionnaires,
        consults=consults,
        prescriptions=prescriptions,
        orders=orders,
        messages=messages,
        seed=seed,
        population_size=population_size,
        span_days=span_days,
    )
