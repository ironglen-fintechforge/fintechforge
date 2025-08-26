from fintechforge.data_models.order import Order, Side, OrderType
from fintechforge.trading_ops.lifecycle import fill_market_order, average_price


def test_fill_market_order():
    order = Order(
        order_id="O-1",
        instrument_id="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
    )
    exec_report = fill_market_order(order, price=100.0)
    assert exec_report.order_id == order.order_id
    assert exec_report.filled_quantity == 10


def test_average_price():
    order = Order(
        order_id="O-2",
        instrument_id="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
    )
    e1 = fill_market_order(order, price=100.0)
    e2 = fill_market_order(order, price=110.0)
    avg = average_price([e1, e2])
    assert avg == 105.0
