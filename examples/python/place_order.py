from fintechforge.data_models.order import Order, Side, OrderType
from fintechforge.trading_ops.lifecycle import fill_market_order


def main() -> None:
    order = Order(
        order_id="O-1001",
        instrument_id="AAPL",
        side=Side.BUY,
        quantity=100,
        order_type=OrderType.MARKET,
    )
    exec_report = fill_market_order(order, price=215.42)
    print(exec_report)


if __name__ == "__main__":
    main()
