from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from fintechforge.data_models.order import Order


@dataclass(frozen=True)
class Execution:
    order_id: str
    exec_id: str
    filled_quantity: float
    price: float
    timestamp_utc: datetime


def fill_market_order(order: Order, price: float) -> Execution:
    order.validate()
    if order.order_type.name != "MARKET":
        raise ValueError("Only MARKET orders supported in this example")
    return Execution(
        order_id=order.order_id,
        exec_id=f"E-{order.order_id}",
        filled_quantity=order.quantity,
        price=price,
        timestamp_utc=datetime.utcnow(),
    )


def average_price(executions: Iterable[Execution]) -> float:
    execs: List[Execution] = list(executions)
    if not execs:
        raise ValueError("No executions provided")
    total_qty = sum(e.filled_quantity for e in execs)
    total_px_qty = sum(e.price * e.filled_quantity for e in execs)
    return total_px_qty / total_qty
