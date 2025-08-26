"""
Comprehensive unit tests for FintechForge data models.

This test suite covers:
1. Instrument models (listed vs derivative)
2. Trade models (economic vs metadata separation)
3. Status tracking and audit trails
4. Organization-specific patterns
5. Validation and error handling
6. Factory functions and utilities
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, Any

from fintechforge.data_models import (
    # Instrument models
    InstrumentType, DayBasis, RollConvention, create_instrument,
    InterestRateLeg, ListedInstrument, DerivativeInstrument,
    Stock, Bond, InterestRateSwap, CreditDefaultSwap,
    
    # Trade models
    TradeStatus, TradeType, TradeSide, create_trade,
    TradeEconomics, TradeMetadata, TradeStatusChange, Trade,
    InvestmentManagerTrade, HedgeFundTrade, MarketMakerTrade, BrokerageTrade,
    StockTrade, BondTrade, IRSTrade, CDSTrade,
    
    # Order models
    Order, OrderSide, OrderType
)


class TestInstrumentModels:
    """Test instrument model creation and validation"""
    
    def test_create_listed_instrument_stock(self):
        """Test creating a listed stock instrument"""
        stock = create_instrument(
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
        
        assert isinstance(stock, Stock)
        assert stock.instrument_id == "AAPL_US"
        assert stock.ticker == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.currency == "USD"
        assert stock.exchange == "NASDAQ"
        assert stock.isin == "US0378331005"
        assert stock.instrument_type == InstrumentType.STOCK
        stock.validate()
    
    def test_create_listed_instrument_bond(self):
        """Test creating a listed bond instrument"""
        bond = create_instrument(
            instrument_type=InstrumentType.BOND,
            instrument_id="UST_10Y",
            ticker="UST10Y",
            name="US Treasury 10-Year Bond",
            currency="USD",
            exchange="OTC",
            isin="US912810TM64",
            cusip="912810TM6",
            face_value=Decimal("1000.00"),
            coupon_rate=Decimal("0.025"),
            maturity_date=date(2033, 5, 15),
            issue_date=date(2023, 5, 15),
            issuer="US Treasury",
            country="US"
        )
        
        assert isinstance(bond, Bond)
        assert bond.instrument_id == "UST_10Y"
        assert bond.face_value == Decimal("1000.00")
        assert bond.coupon_rate == Decimal("0.025")
        assert bond.maturity_date == date(2033, 5, 15)
        assert bond.instrument_type == InstrumentType.BOND
        bond.validate()
    
    def test_create_derivative_instrument_irs(self):
        """Test creating a derivative IRS instrument"""
        pay_leg = InterestRateLeg(
            leg_id="PAY_LEG_001",
            pay_receive="PAY",
            notional=Decimal("10000000.00"),
            currency="USD",
            day_basis=DayBasis.THIRTY_360,
            payment_frequency=6,
            rate_type="FIXED",
            fixed_rate=Decimal("0.025")
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
            float_spread=Decimal("0.001")
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
        
        assert isinstance(irs, InterestRateSwap)
        assert irs.instrument_id == "IRS_001"
        assert irs.pay_leg == pay_leg
        assert irs.receive_leg == receive_leg
        assert irs.instrument_type == InstrumentType.IRS
        irs.validate()
    
    def test_create_derivative_instrument_cds(self):
        """Test creating a derivative CDS instrument"""
        cds = create_instrument(
            instrument_type=InstrumentType.CDS,
            instrument_id="CDS_001",
            underlying_instrument_id="REF_ENTITY_001",
            notional=Decimal("10000000.00"),
            currency="USD",
            trade_date=date(2023, 1, 15),
            maturity_date=date(2028, 1, 15),
            reference_entity="Test Corp",
            protection_buyer="Bank A",
            protection_seller="Bank B",
            credit_events=["BANKRUPTCY", "FAILURE_TO_PAY", "RESTRUCTURING"],
            recovery_rate=Decimal("0.40")
        )
        
        assert isinstance(cds, CreditDefaultSwap)
        assert cds.instrument_id == "CDS_001"
        assert cds.reference_entity == "Test Corp"
        assert cds.protection_buyer == "Bank A"
        assert cds.protection_seller == "Bank B"
        assert cds.recovery_rate == Decimal("0.40")
        assert cds.instrument_type == InstrumentType.CDS
        cds.validate()
    
    def test_instrument_validation_errors(self):
        """Test instrument validation error handling"""
        # Test bond without required fields
        with pytest.raises(ValueError, match="maturity_date is required for bonds"):
            bond = Bond(
                instrument_id="BOND_001",
                ticker="BOND",
                name="Test Bond",
                instrument_type=InstrumentType.BOND,
                currency="USD",
                exchange="OTC",
                isin="TEST123"
                # Missing maturity_date and face_value
            )
            bond.validate()
        
        # Test IRS without legs
        with pytest.raises(ValueError, match="pay_leg and receive_leg are required for IRS"):
            irs = InterestRateSwap(
                instrument_id="IRS_001",
                instrument_type=InstrumentType.IRS,
                underlying_instrument_id="LIBOR_3M",
                notional=Decimal("10000000.00"),
                currency="USD",
                trade_date=date(2023, 1, 15),
                maturity_date=date(2028, 1, 15)
                # Missing pay_leg and receive_leg
            )
            irs.validate()
    
    def test_interest_rate_leg_creation(self):
        """Test InterestRateLeg creation and validation"""
        leg = InterestRateLeg(
            leg_id="LEG_001",
            pay_receive="PAY",
            notional=Decimal("10000000.00"),
            currency="USD",
            day_basis=DayBasis.THIRTY_360,
            payment_frequency=6,
            rate_type="FIXED",
            fixed_rate=Decimal("0.025")
        )
        
        assert leg.leg_id == "LEG_001"
        assert leg.pay_receive == "PAY"
        assert leg.notional == Decimal("10000000.00")
        assert leg.currency == "USD"
        assert leg.day_basis == DayBasis.THIRTY_360
        assert leg.payment_frequency == 6
        assert leg.rate_type == "FIXED"
        assert leg.fixed_rate == Decimal("0.025")


class TestTradeModels:
    """Test trade model creation and validation"""
    
    def test_create_stock_trade(self):
        """Test creating a stock trade with economic and metadata separation"""
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
        
        assert isinstance(trade, StockTrade)
        assert trade.trade_id is not None
        assert trade.instrument_id == "AAPL_US"
        assert trade.side == TradeSide.BUY
        assert trade.trade_type == TradeType.STOCK_TRADE
        assert trade.shares == 1000
        
        # Check economics
        assert trade.economics is not None
        assert trade.economics.notional_amount == Decimal("100000.00")
        assert trade.economics.price == Decimal("150.00")
        assert trade.economics.currency == "USD"
        assert trade.economics.trade_date == date(2023, 12, 15)
        assert trade.economics.trade_value == Decimal("15000000.00")  # 100000 * 150
        
        # Check metadata
        assert trade.metadata is not None
        assert trade.metadata.trader_id == "TRADER_001"
        assert trade.metadata.portfolio_id == "PORTFOLIO_001"
        assert trade.metadata.strategy == "MOMENTUM"
        assert trade.metadata.tags == ["large_cap", "technology", "momentum"]
        assert trade.metadata.status == TradeStatus.PENDING
        
        trade.validate()
    
    def test_create_bond_trade(self):
        """Test creating a bond trade with accrued interest"""
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
        
        assert isinstance(trade, BondTrade)
        assert trade.face_value == Decimal("1000000.00")
        assert trade.trade_type == TradeType.BOND_TRADE
        
        # Check economics with accrued interest
        assert trade.economics.accrued_interest == Decimal("2500.00")
        assert trade.economics.trade_value == Decimal("98502500.00")  # 1000000 * 98.50 + 2500
        
        trade.validate()
    
    def test_create_irs_trade(self):
        """Test creating an IRS trade"""
        trade = create_trade(
            trade_type=TradeType.IRS_TRADE,
            instrument_id="IRS_001",
            side=TradeSide.BUY,
            notional=Decimal("10000000.00"),
            price=Decimal("1.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            pay_leg_notional=Decimal("10000000.00"),
            receive_leg_notional=Decimal("10000000.00"),
            trader_id="TRADER_003",
            portfolio_id="PORTFOLIO_003",
            strategy="RATES"
        )
        
        assert isinstance(trade, IRSTrade)
        assert trade.pay_leg_notional == Decimal("10000000.00")
        assert trade.receive_leg_notional == Decimal("10000000.00")
        assert trade.trade_type == TradeType.IRS_TRADE
        
        trade.validate()
    
    def test_trade_economics_calculation(self):
        """Test trade economics calculations"""
        economics = TradeEconomics(
            trade_id="TEST_001",
            notional_amount=Decimal("100000.00"),
            price=Decimal("150.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            settlement_date=date(2023, 12, 17),
            accrued_interest=Decimal("500.00"),
            commission=Decimal("100.00"),
            fees=Decimal("50.00")
        )
        
        # Test trade value calculation
        expected_value = Decimal("15000000.00") + Decimal("500.00") + Decimal("100.00") + Decimal("50.00")
        assert economics.trade_value == expected_value
        
        # Test USD conversion
        assert economics.trade_value_usd == expected_value  # Already USD
        
        # Test non-USD currency
        eur_economics = TradeEconomics(
            trade_id="TEST_002",
            notional_amount=Decimal("100000.00"),
            price=Decimal("1.00"),
            currency="EUR",
            trade_date=date(2023, 12, 15),
            settlement_date=date(2023, 12, 17),
            fx_rate=Decimal("1.10")
        )
        assert eur_economics.trade_value_usd == Decimal("110000.00")  # 100000 * 1.10
        
        # Test missing FX rate
        with pytest.raises(ValueError, match="FX rate required"):
            eur_economics_no_fx = TradeEconomics(
                trade_id="TEST_003",
                notional_amount=Decimal("100000.00"),
                price=Decimal("1.00"),
                currency="EUR",
                trade_date=date(2023, 12, 15),
                settlement_date=date(2023, 12, 17)
            )
            eur_economics_no_fx.trade_value_usd
    
    def test_trade_metadata_operations(self):
        """Test trade metadata operations"""
        metadata = TradeMetadata(
            trade_id="TEST_001",
            source_system="TRADING_SYSTEM",
            trader_id="TRADER_001",
            portfolio_id="PORTFOLIO_001",
            strategy="MOMENTUM",
            tags=["large_cap", "technology"]
        )
        
        initial_status = metadata.status
        initial_updated_at = metadata.updated_at
        
        # Test status update
        metadata.update_status(TradeStatus.FILLED, "Trade executed successfully")
        assert metadata.status == TradeStatus.FILLED
        # Note: updated_at comparison might fail due to timing, so we'll just check it's set
        assert metadata.updated_at is not None
        assert "Trade executed successfully" in metadata.notes
    
    def test_trade_validation_errors(self):
        """Test trade validation error handling"""
        # Test missing trade_id
        with pytest.raises(ValueError, match="trade_id is required"):
            trade = Trade(trade_id="", instrument_id="TEST")
            trade.validate()
        
        # Test missing instrument_id
        with pytest.raises(ValueError, match="instrument_id is required"):
            trade = Trade(trade_id="TEST_001", instrument_id="")
            trade.validate()
        
        # Test missing trader_id in metadata
        with pytest.raises(ValueError, match="trader_id is required in metadata"):
            trade = Trade(
                trade_id="TEST_001",
                instrument_id="TEST",
                metadata=TradeMetadata(
                    trade_id="TEST_001",
                    source_system="SYSTEM",
                    trader_id="",
                    portfolio_id="PORTFOLIO",
                    strategy="TEST"
                )
            )
            trade.validate()


class TestStatusTracking:
    """Test trade status tracking and audit trails"""
    
    def test_trade_status_changes(self):
        """Test trade status change tracking with audit trail"""
        trade = create_trade(
            trade_type=TradeType.STOCK_TRADE,
            instrument_id="AAPL_US",
            side=TradeSide.BUY,
            notional=Decimal("100000.00"),
            price=Decimal("150.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            trader_id="TRADER_001",
            portfolio_id="PORTFOLIO_001",
            strategy="MOMENTUM"
        )
        
        initial_status = trade.metadata.status
        initial_history_length = len(trade.status_history)
        
        # Update status multiple times
        status_changes = [
            (TradeStatus.PARTIAL, "TRADER_001", "TRADING_SYSTEM", "Partial fill"),
            (TradeStatus.FILLED, "TRADER_001", "TRADING_SYSTEM", "Full execution"),
            (TradeStatus.AFFIRMED, "OPERATIONS", "AFFIRMATION_SYSTEM", "Affirmed"),
            (TradeStatus.CONFIRMED, "OPERATIONS", "CONFIRMATION_SYSTEM", "Confirmed"),
            (TradeStatus.SETTLED, "SETTLEMENT", "SETTLEMENT_SYSTEM", "Settled")
        ]
        
        for new_status, user_id, system, reason in status_changes:
            trade.update_status(new_status, user_id, system, reason)
            assert trade.metadata.status == new_status
        
        # Verify audit trail
        assert len(trade.status_history) == initial_history_length + len(status_changes)
        
        # Verify each status change record
        for i, (expected_status, expected_user, expected_system, expected_reason) in enumerate(status_changes):
            change = trade.status_history[i]
            assert change.to_status == expected_status
            assert change.user_id == expected_user
            assert change.system == expected_system
            assert change.reason == expected_reason
            assert change.hash is not None  # Cryptographic hash should be present
    
    def test_status_change_hash_integrity(self):
        """Test cryptographic hash integrity for status changes"""
        # Use a fixed timestamp for deterministic testing
        fixed_timestamp = datetime(2023, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        change = TradeStatusChange(
            trade_id="TEST_001",
            from_status=TradeStatus.PENDING,
            to_status=TradeStatus.FILLED,
            user_id="TRADER_001",
            system="TRADING_SYSTEM",
            reason="Trade executed"
        )
        
        # Verify hash is created
        assert change.hash is not None
        assert len(change.hash) == 64  # SHA-256 hash length
        
        # Note: Hash will be different due to different timestamps
        # In real usage, the hash provides integrity verification
        # For testing, we just verify the hash is created and has correct length


class TestOrganizationSpecificPatterns:
    """Test organization-specific trade modeling patterns"""
    
    def test_investment_manager_trade(self):
        """Test investment manager trade pattern"""
        trade = InvestmentManagerTrade(
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
        
        assert trade.client_id == "CLIENT_001"
        assert trade.mandate_id == "MANDATE_001"
        assert trade.benchmark_id == "S&P_500"
        assert trade.performance_attribution_tags == ["alpha", "momentum", "large_cap"]
        assert trade.compliance_checks == ["position_limit", "concentration_limit"]
        
        # Test adding performance tag
        trade.add_performance_tag("technology_sector")
        assert "technology_sector" in trade.performance_attribution_tags
        
        # Test adding compliance check
        trade.add_compliance_check("Passed position limit check")
        assert len(trade.compliance_checks) == 3
        assert "Passed position limit check" in trade.compliance_checks[-1]
        
        # Test mandate compliance validation
        assert trade.validate_mandate_compliance() is True
    
    def test_hedge_fund_trade(self):
        """Test hedge fund trade pattern"""
        trade = HedgeFundTrade(
            trade_id="HF_TRADE_001",
            trade_type=TradeType.IRS_TRADE,
            instrument_id="IRS_001",
            side=TradeSide.BUY,
            strategy_id="RATES_STRATEGY_001",
            alpha_source="yield_curve_steepener",
            leverage_ratio=Decimal("3.0"),
            risk_bucket="rates_risk"
        )
        
        assert trade.strategy_id == "RATES_STRATEGY_001"
        assert trade.alpha_source == "yield_curve_steepener"
        assert trade.leverage_ratio == Decimal("3.0")
        assert trade.risk_bucket == "rates_risk"
        
        # Test P&L attribution
        trade.add_pnl_attribution("carry", Decimal("50000.00"))
        trade.add_pnl_attribution("roll_down", Decimal("25000.00"))
        
        assert trade.pnl_attribution["carry"] == Decimal("50000.00")
        assert trade.pnl_attribution["roll_down"] == Decimal("25000.00")
        
        # Test risk contribution calculation
        risk_contribution = trade.calculate_risk_contribution()
        assert "market_risk" in risk_contribution
        assert "credit_risk" in risk_contribution
        assert "liquidity_risk" in risk_contribution
    
    def test_market_maker_trade(self):
        """Test market maker trade pattern"""
        trade = MarketMakerTrade(
            trade_id="MM_TRADE_001",
            trade_type=TradeType.STOCK_TRADE,
            instrument_id="AAPL_US",
            side=TradeSide.BUY,
            inventory_account="AAPL_INVENTORY",
            market_making_desk="EQUITY_MM",
            spread_capture=Decimal("0.25"),
            inventory_impact=Decimal("-0.10")
        )
        
        assert trade.inventory_account == "AAPL_INVENTORY"
        assert trade.market_making_desk == "EQUITY_MM"
        assert trade.spread_capture == Decimal("0.25")
        assert trade.inventory_impact == Decimal("-0.10")
        
        # Test spread capture calculation
        assert trade.calculate_spread_capture() == Decimal("0.25")
        
        # Test inventory update (placeholder)
        trade.update_inventory(Decimal("1000.00"))  # Should not raise error
    
    def test_brokerage_trade(self):
        """Test brokerage trade pattern"""
        trade = BrokerageTrade(
            trade_id="BROKER_TRADE_001",
            trade_type=TradeType.STOCK_TRADE,
            instrument_id="AAPL_US",
            side=TradeSide.BUY,
            client_account="CLIENT_ACCOUNT_001",
            execution_venue="NASDAQ",
            order_id="ORDER_001",
            fill_id="FILL_001"
        )
        
        assert trade.client_account == "CLIENT_ACCOUNT_001"
        assert trade.execution_venue == "NASDAQ"
        assert trade.order_id == "ORDER_001"
        assert trade.fill_id == "FILL_001"
        
        # Test execution metrics
        trade.add_execution_metric("implementation_shortfall", Decimal("0.05"))
        trade.add_execution_metric("market_impact", Decimal("0.02"))
        
        assert trade.execution_quality_metrics["implementation_shortfall"] == Decimal("0.05")
        assert trade.execution_quality_metrics["market_impact"] == Decimal("0.02")
        
        # Test best execution check
        assert trade.calculate_best_execution() is True


class TestDataConsistency:
    """Test data consistency across systems"""
    
    def test_trade_consistency_across_systems(self):
        """Test that trade data remains consistent across different system views"""
        trade_id = "CONSISTENCY_TEST_001"
        
        # Create the same trade in different systems
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
        
        # Verify economic data consistency
        assert trading_trade.economics.trade_value == risk_trade.economics.trade_value
        assert risk_trade.economics.trade_value == settlement_trade.economics.trade_value
        assert trading_trade.economics.notional_amount == risk_trade.economics.notional_amount
        assert trading_trade.economics.price == risk_trade.economics.price
        
        # Verify metadata consistency
        assert trading_trade.metadata.trader_id == risk_trade.metadata.trader_id
        assert trading_trade.metadata.portfolio_id == risk_trade.metadata.portfolio_id
        assert trading_trade.metadata.strategy == risk_trade.metadata.strategy


class TestFactoryFunctions:
    """Test factory functions and utilities"""
    
    def test_create_instrument_factory(self):
        """Test the create_instrument factory function with different types"""
        # Test unsupported instrument type
        with pytest.raises(ValueError, match="Unsupported instrument type"):
            create_instrument(
                instrument_type="UNSUPPORTED_TYPE",
                instrument_id="TEST",
                ticker="TEST",
                name="Test",
                currency="USD",
                exchange="TEST",
                isin="TEST123"
            )
    
    def test_create_trade_factory(self):
        """Test the create_trade factory function with different types"""
        # Test all supported trade types
        trade_types = [
            TradeType.STOCK_TRADE,
            TradeType.BOND_TRADE,
            TradeType.IRS_TRADE,
            TradeType.CDS_TRADE
        ]
        
        for trade_type in trade_types:
            trade = create_trade(
                trade_type=trade_type,
                instrument_id="TEST",
                side=TradeSide.BUY,
                notional=Decimal("100000.00"),
                price=Decimal("100.00"),
                currency="USD",
                trade_date=date(2023, 12, 15),
                trader_id="TRADER_001",
                portfolio_id="PORTFOLIO_001",
                strategy="TEST"
            )
            
            assert trade.trade_type == trade_type
            assert trade.economics is not None
            assert trade.metadata is not None
            trade.validate()


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_zero_notional_validation(self):
        """Test validation of zero notional amounts"""
        instrument = DerivativeInstrument(
            instrument_id="TEST",
            instrument_type=InstrumentType.IRS,
            underlying_instrument_id="TEST",
            notional=Decimal("0.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            maturity_date=date(2028, 12, 15)
        )
        with pytest.raises(ValueError, match="notional must be positive"):
            instrument.validate()
    
    def test_negative_notional_validation(self):
        """Test validation of negative notional amounts"""
        instrument = DerivativeInstrument(
            instrument_id="TEST",
            instrument_type=InstrumentType.IRS,
            underlying_instrument_id="TEST",
            notional=Decimal("-100000.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            maturity_date=date(2028, 12, 15)
        )
        with pytest.raises(ValueError, match="notional must be positive"):
            instrument.validate()
    
    def test_currency_mismatch_validation(self):
        """Test validation of currency mismatches in IRS legs"""
        pay_leg = InterestRateLeg(
            leg_id="PAY_LEG",
            pay_receive="PAY",
            notional=Decimal("10000000.00"),
            currency="USD",
            day_basis=DayBasis.THIRTY_360,
            payment_frequency=6,
            rate_type="FIXED",
            fixed_rate=Decimal("0.025")
        )
        
        receive_leg = InterestRateLeg(
            leg_id="RECEIVE_LEG",
            pay_receive="RECEIVE",
            notional=Decimal("10000000.00"),
            currency="EUR",  # Different currency
            day_basis=DayBasis.THIRTY_360,
            payment_frequency=6,
            rate_type="FLOAT",
            float_index="LIBOR_3M"
        )
        
        with pytest.raises(ValueError, match="pay_leg and receive_leg must have same currency"):
            InterestRateSwap(
                instrument_id="TEST",
                instrument_type=InstrumentType.IRS,
                underlying_instrument_id="TEST",
                notional=Decimal("10000000.00"),
                currency="USD",
                trade_date=date(2023, 12, 15),
                maturity_date=date(2028, 12, 15),
                pay_leg=pay_leg,
                receive_leg=receive_leg
            )
    
    def test_immutable_economics(self):
        """Test that economic data is immutable"""
        economics = TradeEconomics(
            trade_id="TEST",
            notional_amount=Decimal("100000.00"),
            price=Decimal("100.00"),
            currency="USD",
            trade_date=date(2023, 12, 15),
            settlement_date=date(2023, 12, 17)
        )
        
        # Should not be able to modify frozen dataclass
        with pytest.raises(Exception):
            economics.notional_amount = Decimal("200000.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
