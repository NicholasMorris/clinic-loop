"""The documented intent enum for inbound patient messages."""

from enum import Enum


class Intent(str, Enum):
    """Intent labels; `unknown` is the safe value for an unparseable classification."""

    order_status = "order_status"
    cancellation = "cancellation"
    delivery_problem = "delivery_problem"
    general_question = "general_question"
    dose_question = "dose_question"
    adverse_event = "adverse_event"
    pregnancy = "pregnancy"
    mental_health_distress = "mental_health_distress"
    product_name_request = "product_name_request"
    prompt_injection = "prompt_injection"
    unknown = "unknown"


INTENT_DEFINITIONS: dict[Intent, str] = {
    Intent.order_status: "asks where an order is, or when it will ship or arrive",
    Intent.cancellation: "wants to cancel an order, a delivery or a subscription",
    Intent.delivery_problem: (
        "an order arrived damaged, incomplete, wrong or late, or did not arrive at all"
    ),
    Intent.general_question: (
        "general questions about the service: payments, refunds, privacy, opening hours, "
        "changing an address or account details"
    ),
    Intent.dose_question: (
        "asks how much, how often or when to take a medicine, or what to do about a missed dose"
    ),
    Intent.adverse_event: (
        "reports a symptom, reaction or side effect that they connect to a medicine"
    ),
    Intent.pregnancy: "mentions being pregnant, trying to conceive or breastfeeding",
    Intent.mental_health_distress: (
        "expresses distress, hopelessness or thoughts of harming themselves"
    ),
    Intent.product_name_request: (
        "asks which specific medicine, brand or product is prescribed, or asks for one by name"
    ),
    Intent.prompt_injection: (
        "tries to give the assistant instructions, change its rules or reveal its instructions"
    ),
}
