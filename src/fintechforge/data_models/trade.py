from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import hashlib
import uuid


class TradeStatus(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    AFFIRMED = "AFFIRMED"
    CONFIRMED = "CONFIRMED"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TradeType(str, Enum):
    STOCK_TRADE = "STOCK_TRADE"
    BOND_TRADE = "BOND_TRADE"
    IRS_TRADE = "IRS_TRADE"
    CDS_TRADE = "CDS_TRADE"
    FX_TRADE = "FX_TRADE"
    OPTION_TRADE = "OPTION_TRADE"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class TradeEconomics:
    """Immutable economic data used for P&L calculations and risk management"""
    trade_id: str
    notional_amount: Decimal
    price: Decimal
    currency: str
    trade_date: date
    settlement_date: date
    accrued_interest: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    fx_rate: Optional[Decimal] = None  # For cross-currency trades
    
    @property
    def trade_value(self) -> Decimal:
        """Calculate the total trade value"""
        # For bonds, price is typically a percentage (e.g., 98.50 = 98.5%)
        # For stocks, price is typically the actual price per share
        # We'll assume price is the actual price unless it's a bond trade
        base_value = self.notional_amount * self.price
        if self.accrued_interest:
            base_value += self.accrued_interest
        if self.commission:
            base_value += self.commission
        if self.fees:
            base_value += self.fees
        return base_value
    
    @property
    def trade_value_usd(self) -> Decimal:
        """Calculate trade value in USD"""
        if self.currency == "USD":
            return self.trade_value
        elif self.fx_rate:
            return self.trade_value * self.fx_rate
        else:
            raise ValueError("FX rate required for non-USD currency conversion")


@dataclass
class TradeMetadata:
    """Mutable metadata used for operational tracking and workflow management"""
    trade_id: str
    source_system: str
    trader_id: str
    portfolio_id: str
    strategy: str
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: TradeStatus = TradeStatus.PENDING
    
    def update_status(self, new_status: TradeStatus, reason: Optional[str] = None):
        """Update trade status and metadata"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if reason:
            self.notes = f"{self.notes or ''}\n{datetime.utcnow()}: {reason}"


@dataclass
class TradeStatusChange:
    """Record of a status change for audit purposes"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trade_id: str = ""
    from_status: TradeStatus = TradeStatus.PENDING
    to_status: TradeStatus = TradeStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str = ""
    system: str = ""
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    hash: str = field(init=False)
    
    def __post_init__(self):
        """Create cryptographic hash for integrity verification"""
        data = f"{self.change_id}{self.trade_id}{self.from_status}{self.to_status}{self.timestamp.isoformat()}"
        self.hash = hashlib.sha256(data.encode()).hexdigest()


@dataclass
class Trade:
    """Base trade class with economic and metadata separation"""
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trade_type: TradeType = TradeType.STOCK_TRADE
    instrument_id: str = ""
    side: Side = Side.BUY
    
    # Core components
    economics: Optional[TradeEconomics] = None
    metadata: Optional[TradeMetadata] = None
    status_history: List[TradeStatusChange] = field(default_factory=list)
    
    # Audit trail
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Initialize trade with default components if not provided"""
        if self.metadata is None:
            self.metadata = TradeMetadata(
                trade_id=self.trade_id,
                source_system="SYSTEM",
                trader_id="UNKNOWN",
                portfolio_id="UNKNOWN",
                strategy="UNKNOWN"
            )
    
    def update_status(self, new_status: TradeStatus, user_id: str, system: str, reason: Optional[str] = None):
        """Update trade status with audit trail"""
        if self.metadata:
            old_status = self.metadata.status
            
            # Create status change record
            change = TradeStatusChange(
                trade_id=self.trade_id,
                from_status=old_status,
                to_status=new_status,
                user_id=user_id,
                system=system,
                reason=reason
            )
            self.status_history.append(change)
            
            # Update metadata
            self.metadata.update_status(new_status, reason)
            self.updated_at = datetime.now(timezone.utc)
    
    def validate(self) -> None:
        """Validate trade data"""
        if not self.trade_id:
            raise ValueError("trade_id is required")
        if not self.instrument_id:
            raise ValueError("instrument_id is required")
        if self.economics:
            self.economics.trade_value  # This will validate the economics
        if self.metadata:
            if not self.metadata.trader_id:
                raise ValueError("trader_id is required in metadata")


# Organization-specific trade models

@dataclass
class InvestmentManagerTrade(Trade):
    """Trade model for investment managers with client and mandate tracking"""
    client_id: str = ""
    mandate_id: str = ""
    benchmark_id: Optional[str] = None
    performance_attribution_tags: List[str] = field(default_factory=list)
    compliance_checks: List[str] = field(default_factory=list)
    
    def validate_mandate_compliance(self) -> bool:
        """Validate trade against client mandate restrictions"""
        # This would implement mandate compliance logic
        # For now, return True as placeholder
        return True
    
    def add_performance_tag(self, tag: str):
        """Add performance attribution tag"""
        if tag not in self.performance_attribution_tags:
            self.performance_attribution_tags.append(tag)
    
    def add_compliance_check(self, check: str):
        """Add compliance check record"""
        self.compliance_checks.append(f"{datetime.now(timezone.utc)}: {check}")


@dataclass
class HedgeFundTrade(Trade):
    """Trade model for hedge funds with strategy and risk tracking"""
    strategy_id: str = ""
    alpha_source: str = ""
    leverage_ratio: Decimal = Decimal("1.0")
    risk_bucket: str = ""
    pnl_attribution: Dict[str, Decimal] = field(default_factory=dict)
    
    def calculate_risk_contribution(self) -> Dict[str, Decimal]:
        """Calculate contribution to portfolio risk"""
        # This would implement risk contribution calculation
        # For now, return placeholder
        return {
            "market_risk": Decimal("0.0"),
            "credit_risk": Decimal("0.0"),
            "liquidity_risk": Decimal("0.0")
        }
    
    def add_pnl_attribution(self, component: str, value: Decimal):
        """Add P&L attribution component"""
        self.pnl_attribution[component] = value


@dataclass
class MarketMakerTrade(Trade):
    """Trade model for market makers with inventory and spread tracking"""
    inventory_account: str = ""
    market_making_desk: str = ""
    spread_capture: Decimal = Decimal("0.0")
    inventory_impact: Decimal = Decimal("0.0")
    market_impact: Decimal = Decimal("0.0")
    
    def update_inventory(self, quantity_change: Decimal):
        """Update inventory positions"""
        # This would implement inventory update logic
        pass
    
    def calculate_spread_capture(self) -> Decimal:
        """Calculate spread capture for this trade"""
        # This would implement spread capture calculation
        return self.spread_capture


@dataclass
class BrokerageTrade(Trade):
    """Trade model for brokerages with client and execution tracking"""
    client_account: str = ""
    execution_venue: str = ""
    order_id: Optional[str] = None
    fill_id: Optional[str] = None
    execution_quality_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_execution_metric(self, metric: str, value: Any):
        """Add execution quality metric"""
        self.execution_quality_metrics[metric] = value
    
    def calculate_best_execution(self) -> bool:
        """Check if trade meets best execution requirements"""
        # This would implement best execution logic
        return True


# Specialized trade types

@dataclass
class StockTrade(Trade):
    """Stock trade with equity-specific attributes"""
    shares: int = 0
    market_impact: Optional[Decimal] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.trade_type = TradeType.STOCK_TRADE


@dataclass
class BondTrade(Trade):
    """Bond trade with fixed income-specific attributes"""
    face_value: Decimal = Decimal("0.0")
    dirty_price: Optional[Decimal] = None
    clean_price: Optional[Decimal] = None
    yield_to_maturity: Optional[Decimal] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.trade_type = TradeType.BOND_TRADE


@dataclass
class IRSTrade(Trade):
    """Interest Rate Swap trade with IRS-specific attributes"""
    pay_leg_notional: Decimal = Decimal("0.0")
    receive_leg_notional: Decimal = Decimal("0.0")
    pay_rate: Optional[Decimal] = None
    receive_rate: Optional[Decimal] = None
    day_basis: str = "30/360"
    
    def __post_init__(self):
        super().__post_init__()
        self.trade_type = TradeType.IRS_TRADE


@dataclass
class CDSTrade(Trade):
    """Credit Default Swap trade with CDS-specific attributes"""
    reference_entity: str = ""
    protection_buyer: str = ""
    protection_seller: str = ""
    spread_bps: Decimal = Decimal("0.0")
    recovery_rate: Decimal = Decimal("0.40")
    
    def __post_init__(self):
        super().__post_init__()
        self.trade_type = TradeType.CDS_TRADE


# Factory functions

def create_trade(
    trade_type: TradeType,
    instrument_id: str,
    side: Side,
    notional: Decimal,
    price: Decimal,
    currency: str,
    trade_date: date,
    **kwargs
) -> Trade:
    """Factory function to create appropriate trade type"""
    
    # Create economics
    economics = TradeEconomics(
        trade_id=kwargs.get('trade_id', str(uuid.uuid4())),
        notional_amount=notional,
        price=price,
        currency=currency,
        trade_date=trade_date,
        settlement_date=kwargs.get('settlement_date', trade_date),
        accrued_interest=kwargs.get('accrued_interest'),
        commission=kwargs.get('commission'),
        fees=kwargs.get('fees'),
        fx_rate=kwargs.get('fx_rate')
    )
    
    # Create metadata
    metadata = TradeMetadata(
        trade_id=economics.trade_id,
        source_system=kwargs.get('source_system', 'SYSTEM'),
        trader_id=kwargs.get('trader_id', 'UNKNOWN'),
        portfolio_id=kwargs.get('portfolio_id', 'UNKNOWN'),
        strategy=kwargs.get('strategy', 'UNKNOWN'),
        tags=kwargs.get('tags', [])
    )
    
    # Create appropriate trade type
    if trade_type == TradeType.STOCK_TRADE:
        return StockTrade(
            trade_id=economics.trade_id,
            instrument_id=instrument_id,
            side=side,
            economics=economics,
            metadata=metadata,
            shares=kwargs.get('shares', int(notional))
        )
    elif trade_type == TradeType.BOND_TRADE:
        return BondTrade(
            trade_id=economics.trade_id,
            instrument_id=instrument_id,
            side=side,
            economics=economics,
            metadata=metadata,
            face_value=kwargs.get('face_value', notional)
        )
    elif trade_type == TradeType.IRS_TRADE:
        return IRSTrade(
            trade_id=economics.trade_id,
            instrument_id=instrument_id,
            side=side,
            economics=economics,
            metadata=metadata,
            pay_leg_notional=kwargs.get('pay_leg_notional', notional),
            receive_leg_notional=kwargs.get('receive_leg_notional', notional)
        )
    elif trade_type == TradeType.CDS_TRADE:
        return CDSTrade(
            trade_id=economics.trade_id,
            instrument_id=instrument_id,
            side=side,
            economics=economics,
            metadata=metadata,
            reference_entity=kwargs.get('reference_entity', ''),
            protection_buyer=kwargs.get('protection_buyer', ''),
            protection_seller=kwargs.get('protection_seller', '')
        )
    else:
        return Trade(
            trade_id=economics.trade_id,
            trade_type=trade_type,
            instrument_id=instrument_id,
            side=side,
            economics=economics,
            metadata=metadata
        )


# Example usage
if __name__ == "__main__":
    # Create a stock trade
    stock_trade = create_trade(
        trade_type=TradeType.STOCK_TRADE,
        instrument_id="AAPL_US",
        side=Side.BUY,
        notional=Decimal("100000.00"),
        price=Decimal("150.00"),
        currency="USD",
        trade_date=date(2023, 12, 15),
        shares=1000,
        trader_id="TRADER_001",
        portfolio_id="PORTFOLIO_001",
        strategy="MOMENTUM"
    )
    stock_trade.validate()
    
    # Update status
    stock_trade.update_status(TradeStatus.FILLED, "TRADER_001", "TRADING_SYSTEM", "Trade executed successfully")
    
    # Create a bond trade
    bond_trade = create_trade(
        trade_type=TradeType.BOND_TRADE,
        instrument_id="UST_10Y",
        side=Side.BUY,
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
    bond_trade.validate()
    
    print("All trades created and validated successfully!")
    print(f"Stock trade value: ${stock_trade.economics.trade_value}")
    print(f"Bond trade value: ${bond_trade.economics.trade_value}")
