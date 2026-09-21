"""World builder for SimClinic."""

from typing import NamedTuple

import numpy as np

from ..entities import Consult, Message, Order, Patient, Prescription, Questionnaire
from .fictional_ranges import (
    CLINICIAN_IDS,
    EMAIL_DOMAIN_FICTIONAL,
    EMAIL_LOCAL_CHARS,
    FICTIONAL_FAMILY_NAMES,
    FICTIONAL_GIVEN_NAMES,
    FICTIONAL_POSTCODES,
    FICTIONAL_STREETS,
    HEALTH_ID_FICTIONAL_RANGE,
    HEALTH_ID_PREFIX_FICTIONAL,
    PATIENT_DOB_YEAR_MAX,
    PATIENT_DOB_YEAR_MIN,
    PHONE_AREA_CODE_FICTIONAL,
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

    # Generate patients
    patients = []
    for i in range(population_size):
        patient = _generate_patient(patient_rng, i)
        patients.append(patient)

    # Generate questionnaires (one per patient)
    questionnaires = []
    for i, patient in enumerate(patients):
        questionnaire = _generate_questionnaire(questionnaire_rng, i, patient.patient_id, span_days)
        questionnaires.append(questionnaire)

    # Generate consults (one per patient, scheduled after questionnaire)
    consults = []
    for i, (patient, questionnaire) in enumerate(zip(patients, questionnaires)):
        consult = _generate_consult(
            consult_rng,
            i,
            patient.patient_id,
            questionnaire.questionnaire_id,
            questionnaire.submitted_at_minute,
            span_days,
        )
        consults.append(consult)

    # Generate prescriptions (~30% of consults)
    prescriptions = []
    prescription_count = max(1, int(population_size * 0.3))
    for i in range(prescription_count):
        prescription = _generate_prescription(
            prescription_rng,
            i,
            consults[i].consult_id,
            consults[i].patient_id,
            consults[i].scheduled_at_minute,
        )
        prescriptions.append(prescription)

    # Generate orders (~20% of patients)
    orders = []
    order_count = max(1, int(population_size * 0.2))
    for i in range(order_count):
        if i < len(prescriptions):
            prescription = prescriptions[i]
            order = _generate_order(
                order_rng,
                i,
                prescription.prescription_id,
                prescription.patient_id,
                prescription.issued_at_minute,
                patients[i].market,
            )
            orders.append(order)

    # Generate messages (~50% of patients, spread across days)
    messages = []
    message_count = max(1, int(population_size * 0.5))
    for i in range(message_count):
        message = _generate_message(
            message_rng, i, patients[i % len(patients)].patient_id, span_days
        )
        messages.append(message)

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


def _generate_patient(rng: np.random.Generator, index: int) -> Patient:
    """Generate a single Patient entity.

    Args:
        rng: Random number generator for this stream.
        index: Patient index for ID generation.

    Returns:
        A Patient entity.
    """
    patient_id = f"P{index + 1:06d}"
    market = rng.choice(["AU", "NZ", "UK"])

    # Generate name
    given_name = rng.choice(FICTIONAL_GIVEN_NAMES)
    family_name = rng.choice(FICTIONAL_FAMILY_NAMES)
    full_name = f"{given_name} {family_name}"

    # Generate date of birth (adult only)
    year = int(rng.integers(PATIENT_DOB_YEAR_MIN, PATIENT_DOB_YEAR_MAX + 1))
    month = int(rng.integers(1, 13))
    day = int(rng.integers(1, 29))  # Use safe day to avoid invalid dates
    date_of_birth = f"{year:04d}-{month:02d}-{day:02d}"

    # Generate address
    street_name = rng.choice(FICTIONAL_STREETS)
    street_number = int(rng.integers(1, 1000))
    street_address = f"{street_number} {street_name}"
    postcode = rng.choice(FICTIONAL_POSTCODES)

    # Generate phone number
    phone_suffix = int(rng.integers(0, 10000000))
    phone_number = f"{PHONE_AREA_CODE_FICTIONAL}{phone_suffix:07d}"

    # Generate email
    local_length = int(rng.integers(5, 15))
    local_chars = list(EMAIL_LOCAL_CHARS)
    local_part = "".join(str(rng.choice(local_chars)) for _ in range(local_length))
    email = f"{local_part}@{EMAIL_DOMAIN_FICTIONAL}"

    # Generate health identifier
    health_id_min = min(HEALTH_ID_FICTIONAL_RANGE)
    health_id_max = max(HEALTH_ID_FICTIONAL_RANGE)
    health_id_number = int(rng.integers(health_id_min, health_id_max))
    health_identifier = f"{HEALTH_ID_PREFIX_FICTIONAL}{health_id_number:08d}"

    # Generate payment instrument (small share share same instrument)
    # Approximately 10% share instruments
    if rng.random() < 0.1 and index > 0:
        # Reuse an instrument from earlier patients
        instrument_number = int(rng.integers(1, index // 10 + 2))
    else:
        # Unique instrument
        instrument_number = index + 1
    payment_instrument_id = f"PI{instrument_number:05d}"

    created_at_minute = 0

    return Patient(
        patient_id=patient_id,
        market=market,  # type: ignore
        full_name=full_name,
        date_of_birth=date_of_birth,
        street_address=street_address,
        postcode=postcode,
        phone_number=phone_number,
        email=email,
        health_identifier=health_identifier,
        payment_instrument_id=payment_instrument_id,
        created_at_minute=created_at_minute,
        synthetic=True,
    )


def _generate_questionnaire(
    rng: np.random.Generator,
    index: int,
    patient_id: str,
    span_days: int,
) -> Questionnaire:
    """Generate a single Questionnaire entity.

    Args:
        rng: Random number generator for this stream.
        index: Questionnaire index for ID generation.
        patient_id: Associated patient ID.
        span_days: Number of days in simulation.

    Returns:
        A Questionnaire entity.
    """
    questionnaire_id = f"Q{index + 1:06d}"

    # Spread submissions over span_days with plausible daily pattern
    # More submissions on weekdays (Mon-Fri)
    day = int(rng.integers(0, span_days))
    is_weekday = (day % 7) < 5  # Mon-Fri

    # Busier pattern on weekdays
    if is_weekday:
        hour = int(rng.integers(8, 18))  # Business hours
    else:
        hour = int(rng.integers(0, 24))  # Any hour on weekends

    submitted_at_minute = day * 24 * 60 + hour * 60 + int(rng.integers(0, 60))

    # Generate answers
    reason_templates = [
        "follow-up consultation",
        "initial consultation",
        "prescription renewal",
        "symptom evaluation",
    ]
    answers = {
        "reason_for_care": rng.choice(reason_templates),
        "current_medications": "Aspirin 100mg daily" if rng.random() < 0.7 else "None",
        "allergies": "Penicillin" if rng.random() < 0.2 else "None",
        "previous_treatment": "Previous course" if rng.random() < 0.5 else "None",
    }

    # ~30% reuse a template
    template_id = None
    if rng.random() < 0.3:
        template_id = f"T{rng.integers(1, 10):03d}"

    return Questionnaire(
        questionnaire_id=questionnaire_id,
        patient_id=patient_id,
        submitted_at_minute=submitted_at_minute,
        answers=answers,
        template_id=template_id,
        synthetic=True,
    )


def _generate_consult(
    rng: np.random.Generator,
    index: int,
    patient_id: str,
    questionnaire_id: str,
    questionnaire_minute: int,
    span_days: int,
) -> Consult:
    """Generate a single Consult entity.

    Args:
        rng: Random number generator for this stream.
        index: Consult index for ID generation.
        patient_id: Associated patient ID.
        questionnaire_id: Associated questionnaire ID.
        questionnaire_minute: Time of questionnaire submission.
        span_days: Number of days in simulation.

    Returns:
        A Consult entity.
    """
    consult_id = f"C{index + 1:06d}"
    clinician_id = rng.choice(CLINICIAN_IDS)

    # Schedule after questionnaire, within available span
    questionnaire_day = questionnaire_minute // (24 * 60)
    remaining_days = max(1, span_days - questionnaire_day)
    days_to_schedule = min(7, remaining_days)
    days_after = int(rng.integers(1, max(2, days_to_schedule))) if days_to_schedule > 0 else 1
    scheduled_at_minute = questionnaire_minute + days_after * 24 * 60

    duration_minutes = int(rng.integers(10, 31))

    return Consult(
        consult_id=consult_id,
        patient_id=patient_id,
        questionnaire_id=questionnaire_id,
        clinician_id=clinician_id,
        scheduled_at_minute=scheduled_at_minute,
        duration_minutes=duration_minutes,
        mode="phone",
        status="scheduled",
        synthetic=True,
    )


def _generate_prescription(
    rng: np.random.Generator,
    index: int,
    consult_id: str,
    patient_id: str,
    consult_minute: int,
) -> Prescription:
    """Generate a single Prescription entity.

    Args:
        rng: Random number generator for this stream.
        index: Prescription index for ID generation.
        consult_id: Associated consult ID.
        patient_id: Associated patient ID.
        consult_minute: Time of consult.

    Returns:
        A Prescription entity.
    """
    prescription_id = f"RX{index + 1:06d}"
    issued_at_minute = consult_minute + int(rng.integers(5, 60))

    return Prescription(
        prescription_id=prescription_id,
        consult_id=consult_id,
        patient_id=patient_id,
        issued_at_minute=issued_at_minute,
        status="issued",
        synthetic=True,
    )


def _generate_order(
    rng: np.random.Generator,
    index: int,
    prescription_id: str,
    patient_id: str,
    prescription_minute: int,
    market: str,
) -> Order:
    """Generate a single Order entity.

    Args:
        rng: Random number generator for this stream.
        index: Order index for ID generation.
        prescription_id: Associated prescription ID.
        patient_id: Associated patient ID.
        prescription_minute: Time of prescription.
        market: Market jurisdiction for shipping calculation.

    Returns:
        An Order entity.
    """
    order_id = f"O{index + 1:06d}"
    created_at_minute = prescription_minute + int(rng.integers(10, 120))

    # Generate price
    plan_price_cents = int(rng.integers(1000, 50000))

    # Calculate shipping based on market
    if market == "AU":
        # AU rule: $9.95 flat under $129, free above
        if plan_price_cents < 12900:
            shipping_cents = 995
        else:
            shipping_cents = 0
    else:
        # NZ/UK: use flat rate for now
        shipping_cents = 1500

    return Order(
        order_id=order_id,
        prescription_id=prescription_id,
        patient_id=patient_id,
        created_at_minute=created_at_minute,
        plan_price_cents=plan_price_cents,
        shipping_cents=shipping_cents,
        status="created",
        synthetic=True,
    )


def _generate_message(
    rng: np.random.Generator,
    index: int,
    patient_id: str,
    span_days: int,
) -> Message:
    """Generate a single Message entity.

    Args:
        rng: Random number generator for this stream.
        index: Message index for ID generation.
        patient_id: Associated patient ID.
        span_days: Number of days in simulation.

    Returns:
        A Message entity.
    """
    message_id = f"M{index + 1:06d}"

    # Spread messages across days
    day = int(rng.integers(0, span_days))
    hour = int(rng.integers(0, 24))
    received_at_minute = day * 24 * 60 + hour * 60 + int(rng.integers(0, 60))

    channel_options: list[str] = ["chat", "email"]
    channel = rng.choice(channel_options)
    assert isinstance(channel, str)

    # Generate message body from templates
    message_templates = [
        "Order status update",
        "Delivery confirmation",
        "Cancellation request",
        "General inquiry",
        "Technical issue",
    ]
    body = rng.choice(message_templates)

    return Message(
        message_id=message_id,
        patient_id=patient_id,
        channel=channel,  # type: ignore[arg-type]
        received_at_minute=received_at_minute,
        body=body,
        synthetic=True,
    )
