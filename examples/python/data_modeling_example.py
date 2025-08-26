#!/usr/bin/env python3
"""
Data Modeling Example for Trading Operations

This example demonstrates the key concepts from the data modeling document:
1. Listed vs Derivative Instrument Modeling
2. Economic vs Metadata Attribute Separation
3. Trade Status Change Tracking
4. Organization-Specific Patterns
5. Distributed Information Repositories

Run this example to see how the data models work in practice.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List

from fintechforge.data_models import (
    # Instrument models
    InstrumentType, DayBasis, create_instrument,
    InterestRateLeg,
    
    # Trade models
    TradeType, TradeSide, TradeStatus, create_trade,
    InvestmentManagerTrade, HedgeFundTrade, MarketMakerTrade, BrokerageTrade,
    
    # Order models
    Order, OrderSide, OrderType
)


def demonstrate_listed_vs_derivative_modeling():
    """Demonstrate the difference between listed and derivative instrument modeling"""
    print("=" * 60)
    print("1. LISTED VS DERIVATIVE INSTRUMENT MODELING")
    print("=" * 60)
    
    # Create a listed instrument (stock)
    print("\nCreating a listed instrument (Apple stock):")
    apple_stock = create_instrument(
        instrument_type=InstrumentType.STOCK,
        instrument_id="AAPL_US",
        ticker="AAPL",
        name="Apple Inc.",
        currency="USD",
        exchange="NASDAQ",
        isin="US0378331005",
        cusip="037833100",
        issuer="Apple Inc.",
        sector="Technology",
        country="US"
    )
    apple_stock.validate()
    print(f"✓ Created {apple_stock.instrument_type} instrument: {apple_stock.name}")
    print(f"  - One-to-many relationship: Multiple trades can reference this instrument")
    print(f"  - Standardized terms: {apple_stock.ticker} on {apple_stock.exchange}")
    
    # Create a derivative instrument (IRS)
    print("\nCreating a derivative instrument (Interest Rate Swap):")
    pay_leg = InterestRateLeg(
        leg_id="PAY_LEG_001",
        pay_receive="PAY",
        notional=Decimal("10000000.00"),
        currency="USD",
        day_basis=DayBasis.THIRTY_360,
        payment_frequency=6,
        rate_type="FIXED",
        fixed_rate=Decimal("0.025")  # 2.5%
    )
    
    receive_leg = InterestRateLeg(
        leg_id="RECEIVE_LEG_001",
        pay_receive="RECEIVE",
        notional=Decimal("10000000.00"),
        currency="USD",
        day_basis=DayBasis.THIRTY_360,
        payment_frequency=6,
        rate_type="FLOAT",
        float_index="LIBOR_3M",
        float_spread=Decimal("0.001")  # 10 bps spread
    )
    
    irs = create_instrument(
        instrument_type=InstrumentType.IRS,
        instrument_id="IRS_001",
        underlying_instrument_id="LIBOR_3M",
        notional=Decimal("10000000.00"),
        currency="USD",
        trade_date=date(2023, 1, 15),
        maturity_date=date(2028, 1, 15),
        pay_leg=pay_leg,
        receive_leg=receive_leg
    )
    irs.validate()
    print(f"✓ Created {irs.instrument_type} instrument: {irs.instrument_id}")
    print(f"  - One-to-one relationship: Each trade creates a unique contract")
    print(f"  - Complex terms: Pay {pay_leg.fixed_rate}%, Receive {receive_leg.float_index} + {receive_leg.float_spread}")


def demonstrate_economic_vs_metadata_separation():
    """Demonstrate the separation of economic and metadata attributes"""
    print("\n" + "=" * 60)
    print("2. ECONOMIC VS METADATA ATTRIBUTE SEPARATION")
    print("=" * 60)
    
    # Create a trade with separated economics and metadata
    print("\nCreating a trade with separated economics and metadata:")
    trade = create_trade(
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        notional=Decimal("100000.00"),
        price=Decimal("150.00"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        shares=1000,
        trader_id="TRADER_001",
        portfolio_id="PORTFOLIO_001",
        strategy="MOMENTUM",
        tags=["large_cap", "technology", "momentum"]
    )
    
    print(f"✓ Created trade: {trade.trade_id}")
    print("\nEconomic Attributes (Immutable, for P&L calculations):")
    print(f"  - Notional: ${trade.economics.notional_amount:,.2f}")
    print(f"  - Price: ${trade.economics.price}")
    print(f"  - Trade Value: ${trade.economics.trade_value:,.2f}")
    print(f"  - Currency: {trade.economics.currency}")
    print(f"  - Trade Date: {trade.economics.trade_date}")
    
    print("\nMetadata Attributes (Mutable, for operational tracking):")
    print(f"  - Trader: {trade.metadata.trader_id}")
    print(f"  - Portfolio: {trade.metadata.portfolio_id}")
    print(f"  - Strategy: {trade.metadata.strategy}")
    print(f"  - Tags: {trade.metadata.tags}")
    print(f"  - Status: {trade.metadata.status}")
    print(f"  - Created: {trade.metadata.created_at}")


def demonstrate_status_tracking():
    """Demonstrate trade status change tracking with audit trail"""
    print("\n" + "=" * 60)
    print("3. TRADE STATUS CHANGE TRACKING")
    print("=" * 60)
    
    # Create a trade and track status changes
    trade = create_trade(
        trade_type=TradeType.BOND_TRADE,
        instrument_id="UST_10Y",
        side=TradeSide.BUY,
        notional=Decimal("1000000.00"),
        price=Decimal("98.50"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        face_value=Decimal("1000000.00"),
        accrued_interest=Decimal("2500.00"),
        trader_id="TRADER_002",
        portfolio_id="PORTFOLIO_002",
        strategy="INCOME"
    )
    
    print(f"\nCreated trade: {trade.trade_id}")
    print(f"Initial status: {trade.metadata.status}")
    
    # Simulate trade lifecycle
    status_changes = [
        (TradeStatus.PARTIAL, "TRADER_002", "TRADING_SYSTEM", "Partial fill received"),
        (TradeStatus.FILLED, "TRADER_002", "TRADING_SYSTEM", "Trade fully executed"),
        (TradeStatus.AFFIRMED, "OPERATIONS", "AFFIRMATION_SYSTEM", "Trade affirmed by counterparty"),
        (TradeStatus.CONFIRMED, "OPERATIONS", "CONFIRMATION_SYSTEM", "Trade confirmed"),
        (TradeStatus.SETTLED, "SETTLEMENT", "SETTLEMENT_SYSTEM", "Trade settled")
    ]
    
    for new_status, user_id, system, reason in status_changes:
        trade.update_status(new_status, user_id, system, reason)
        print(f"Status updated to: {new_status} by {user_id} via {system}")
    
    print(f"\nFinal status: {trade.metadata.status}")
    print(f"Total status changes: {len(trade.status_history)}")
    
    print("\nStatus Change History:")
    for i, change in enumerate(trade.status_history, 1):
        print(f"  {i}. {change.from_status} → {change.to_status}")
        print(f"     Time: {change.timestamp}")
        print(f"     User: {change.user_id} via {change.system}")
        print(f"     Reason: {change.reason}")
        print(f"     Hash: {change.hash[:16]}...")


def demonstrate_organization_specific_patterns():
    """Demonstrate organization-specific trade modeling patterns"""
    print("\n" + "=" * 60)
    print("4. ORGANIZATION-SPECIFIC MODELING PATTERNS")
    print("=" * 60)
    
    # Investment Manager Trade
    print("\nInvestment Manager Trade Pattern:")
    im_trade = InvestmentManagerTrade(
        trade_id="IM_TRADE_001",
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        client_id="CLIENT_001",
        mandate_id="MANDATE_001",
        benchmark_id="S&P_500",
        performance_attribution_tags=["alpha", "momentum", "large_cap"],
        compliance_checks=["position_limit", "concentration_limit"]
    )
    im_trade.add_performance_tag("technology_sector")
    im_trade.add_compliance_check("Passed position limit check")
    print(f"✓ Created IM trade with client {im_trade.client_id}")
    print(f"  - Mandate: {im_trade.mandate_id}")
    print(f"  - Performance tags: {im_trade.performance_attribution_tags}")
    print(f"  - Compliance checks: {im_trade.compliance_checks}")
    
    # Hedge Fund Trade
    print("\nHedge Fund Trade Pattern:")
    hf_trade = HedgeFundTrade(
        trade_id="HF_TRADE_001",
        trade_type=TradeType.IRS_TRADE,
        instrument_id="IRS_001",
        side=TradeSide.BUY,
        strategy_id="RATES_STRATEGY_001",
        alpha_source="yield_curve_steepener",
        leverage_ratio=Decimal("3.0"),
        risk_bucket="rates_risk"
    )
    hf_trade.add_pnl_attribution("carry", Decimal("50000.00"))
    hf_trade.add_pnl_attribution("roll_down", Decimal("25000.00"))
    print(f"✓ Created HF trade with strategy {hf_trade.strategy_id}")
    print(f"  - Alpha source: {hf_trade.alpha_source}")
    print(f"  - Leverage: {hf_trade.leverage_ratio}x")
    print(f"  - P&L attribution: {hf_trade.pnl_attribution}")
    
    # Market Maker Trade
    print("\nMarket Maker Trade Pattern:")
    mm_trade = MarketMakerTrade(
        trade_id="MM_TRADE_001",
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        inventory_account="AAPL_INVENTORY",
        market_making_desk="EQUITY_MM",
        spread_capture=Decimal("0.25"),  # 25 cents spread capture
        inventory_impact=Decimal("-0.10")  # 10 cents inventory impact
    )
    print(f"✓ Created MM trade for desk {mm_trade.market_making_desk}")
    print(f"  - Inventory account: {mm_trade.inventory_account}")
    print(f"  - Spread capture: ${mm_trade.spread_capture}")
    print(f"  - Inventory impact: ${mm_trade.inventory_impact}")
    
    # Brokerage Trade
    print("\nBrokerage Trade Pattern:")
    broker_trade = BrokerageTrade(
        trade_id="BROKER_TRADE_001",
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        client_account="CLIENT_ACCOUNT_001",
        execution_venue="NASDAQ",
        order_id="ORDER_001",
        fill_id="FILL_001"
    )
    broker_trade.add_execution_metric("implementation_shortfall", Decimal("0.05"))
    broker_trade.add_execution_metric("market_impact", Decimal("0.02"))
    print(f"✓ Created broker trade for client {broker_trade.client_account}")
    print(f"  - Execution venue: {broker_trade.execution_venue}")
    print(f"  - Execution metrics: {broker_trade.execution_quality_metrics}")


def demonstrate_data_consistency():
    """Demonstrate data consistency across systems"""
    print("\n" + "=" * 60)
    print("5. DATA CONSISTENCY ACROSS SYSTEMS")
    print("=" * 60)
    
    # Simulate multiple systems with the same trade data
    trade_id = "CONSISTENCY_TEST_001"
    
    # Trading System
    trading_trade = create_trade(
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        notional=Decimal("100000.00"),
        price=Decimal("150.00"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        trade_id=trade_id,
        trader_id="TRADER_001",
        portfolio_id="PORTFOLIO_001",
        strategy="MOMENTUM"
    )
    
    # Risk System (same trade, different view)
    risk_trade = create_trade(
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        notional=Decimal("100000.00"),
        price=Decimal("150.00"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        trade_id=trade_id,
        trader_id="TRADER_001",
        portfolio_id="PORTFOLIO_001",
        strategy="MOMENTUM"
    )
    
    # Settlement System (same trade, different view)
    settlement_trade = create_trade(
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=TradeSide.BUY,
        notional=Decimal("100000.00"),
        price=Decimal("150.00"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        trade_id=trade_id,
        trader_id="TRADER_001",
        portfolio_id="PORTFOLIO_001",
        strategy="MOMENTUM"
    )
    
    print(f"✓ Created trade {trade_id} across three systems")
    print("\nData Consistency Check:")
    print(f"  Trading System - Trade Value: ${trading_trade.economics.trade_value:,.2f}")
    print(f"  Risk System - Trade Value: ${risk_trade.economics.trade_value:,.2f}")
    print(f"  Settlement System - Trade Value: ${settlement_trade.economics.trade_value:,.2f}")
    
    # Verify consistency
    values_consistent = (
        trading_trade.economics.trade_value == 
        risk_trade.economics.trade_value == 
        settlement_trade.economics.trade_value
    )
    print(f"\nConsistency Check: {'✓ PASSED' if values_consistent else '✗ FAILED'}")


def main():
    """Run all demonstrations"""
    print("FINtechForge Data Modeling Example")
    print("Demonstrating key concepts from the data modeling document")
    print("=" * 80)
    
    try:
        demonstrate_listed_vs_derivative_modeling()
        demonstrate_economic_vs_metadata_separation()
        demonstrate_status_tracking()
        demonstrate_organization_specific_patterns()
        demonstrate_data_consistency()
        
        print("\n" + "=" * 80)
        print("✓ All demonstrations completed successfully!")
        print("\nKey Takeaways:")
        print("1. Listed instruments have one-to-many relationships with trades")
        print("2. Derivative instruments have one-to-one relationships with trades")
        print("3. Economic data is immutable and used for P&L calculations")
        print("4. Metadata is mutable and used for operational tracking")
        print("5. Status changes are tracked with cryptographic audit trails")
        print("6. Different organizations have different modeling requirements")
        print("7. Data consistency across systems is critical")
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()
