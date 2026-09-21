"""Pydantic schemas for order endpoints."""

from pydantic import BaseModel


class OrderRead(BaseModel):
    """Response schema for order reads.

    Attributes:
        order_id: Order identifier.
        prescription_id: Prescription identifier.
        patient_id: Patient identifier.
        created_at_minute: Creation time in sim-minutes.
        plan_price_cents: Price in cents.
        shipping_cents: Shipping cost in cents.
        status: Order status.
        synthetic: Always True.
    """

    order_id: str
    prescription_id: str
    patient_id: str
    created_at_minute: int
    plan_price_cents: int
    shipping_cents: int
    status: str
    synthetic: bool
