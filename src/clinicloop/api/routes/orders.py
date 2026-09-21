"""Order endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from clinicloop.world.generator.build import World

from ..schemas.order import OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


def get_world() -> World:
    """Get the world dependency.

    This will be overridden by the app.
    """
    raise NotImplementedError()  # pragma: no cover


@router.get("", response_model=list[OrderRead])
def get_orders(world: World = Depends(get_world)) -> list[OrderRead]:
    """Get all orders from the snapshot.

    Args:
        world: The loaded world snapshot (injected).

    Returns:
        List of OrderRead schemas.
    """
    return [
        OrderRead(
            order_id=o.order_id,
            prescription_id=o.prescription_id,
            patient_id=o.patient_id,
            created_at_minute=o.created_at_minute,
            plan_price_cents=o.plan_price_cents,
            shipping_cents=o.shipping_cents,
            status=o.status,
            synthetic=o.synthetic,
        )
        for o in world.orders
    ]


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: str, world: World = Depends(get_world)) -> OrderRead:
    """Get an order by ID.

    Args:
        order_id: The order identifier.
        world: The loaded world snapshot (injected).

    Returns:
        The OrderRead schema for the order.

    Raises:
        HTTPException: 404 if order not found.
    """
    order = next((o for o in world.orders if o.order_id == order_id), None)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"Order {order_id} not found",
        )

    return OrderRead(
        order_id=order.order_id,
        prescription_id=order.prescription_id,
        patient_id=order.patient_id,
        created_at_minute=order.created_at_minute,
        plan_price_cents=order.plan_price_cents,
        shipping_cents=order.shipping_cents,
        status=order.status,
        synthetic=order.synthetic,
    )
