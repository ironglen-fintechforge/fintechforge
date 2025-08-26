from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class InstrumentType(str, Enum):
    # Listed instruments
    STOCK = "STOCK"
    BOND = "BOND"
    ETF = "ETF"
    MONEY_MARKET = "MONEY_MARKET"
    
    # Derivative instruments
    IRS = "IRS"  # Interest Rate Swap
    CDS = "CDS"  # Credit Default Swap
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    FORWARD = "FORWARD"


class DayBasis(str, Enum):
    ACTUAL_360 = "ACTUAL_360"
    ACTUAL_365 = "ACTUAL_365"
    ACTUAL_ACTUAL = "ACTUAL_ACTUAL"
    THIRTY_360 = "THIRTY_360"
    THIRTY_365 = "THIRTY_365"


class RollConvention(str, Enum):
    MODIFIED_FOLLOWING = "MODIFIED_FOLLOWING"
    FOLLOWING = "FOLLOWING"
    PRECEDING = "PRECEDING"
    MODIFIED_PRECEDING = "MODIFIED_PRECEDING"


@dataclass(frozen=True)
class InterestRateLeg:
    """Represents one leg of an interest rate swap"""
    leg_id: str
    pay_receive: str  # "PAY" or "RECEIVE"
    notional: Decimal
    currency: str
    day_basis: DayBasis
    payment_frequency: int  # months between payments
    rate_type: str  # "FIXED" or "FLOAT"
    fixed_rate: Optional[Decimal] = None
    float_index: Optional[str] = None
    float_spread: Optional[Decimal] = None
    first_fixing_date: Optional[date] = None
    last_fixing_date: Optional[date] = None


@dataclass(frozen=True)
class ListedInstrument:
    """Base class for listed instruments (stocks, bonds, ETFs)"""
    instrument_id: str
    ticker: str
    name: str
    instrument_type: InstrumentType
    currency: str
    exchange: str
    isin: str
    cusip: Optional[str] = None
    
    # Standard attributes
    face_value: Optional[Decimal] = None
    coupon_rate: Optional[Decimal] = None
    maturity_date: Optional[date] = None
    issue_date: Optional[date] = None
    
    # Metadata
    issuer: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    
    def validate(self) -> None:
        """Validate instrument data"""
        if not self.instrument_id:
            raise ValueError("instrument_id is required")
        if not self.ticker:
            raise ValueError("ticker is required")
        if not self.isin:
            raise ValueError("isin is required")
        
        # Type-specific validation
        if self.instrument_type == InstrumentType.BOND:
            if not self.maturity_date:
                raise ValueError("maturity_date is required for bonds")
            if not self.face_value:
                raise ValueError("face_value is required for bonds")


@dataclass(frozen=True)
class DerivativeInstrument:
    """Base class for derivative instruments (IRS, CDS, options)"""
    instrument_id: str
    instrument_type: InstrumentType
    underlying_instrument_id: str
    notional: Decimal
    currency: str
    trade_date: date
    maturity_date: date
    contract_terms: Dict[str, Any] = field(default_factory=dict)
    
    # IRS-specific attributes
    pay_leg: Optional[InterestRateLeg] = None
    receive_leg: Optional[InterestRateLeg] = None
    
    # CDS-specific attributes
    reference_entity: Optional[str] = None
    credit_events: Optional[List[str]] = None
    protection_buyer: Optional[str] = None
    protection_seller: Optional[str] = None
    
    def validate(self) -> None:
        """Validate derivative instrument data"""
        if not self.instrument_id:
            raise ValueError("instrument_id is required")
        if not self.underlying_instrument_id:
            raise ValueError("underlying_instrument_id is required")
        if self.notional <= 0:
            raise ValueError("notional must be positive")
        
        # Type-specific validation
        if self.instrument_type == InstrumentType.IRS:
            if not self.pay_leg or not self.receive_leg:
                raise ValueError("pay_leg and receive_leg are required for IRS")
            if self.pay_leg.currency != self.receive_leg.currency:
                raise ValueError("pay_leg and receive_leg must have same currency")
        
        elif self.instrument_type == InstrumentType.CDS:
            if not self.reference_entity:
                raise ValueError("reference_entity is required for CDS")
            if not self.protection_buyer or not self.protection_seller:
                raise ValueError("protection_buyer and protection_seller are required for CDS")


@dataclass(frozen=True)
class Stock(ListedInstrument):
    """Stock instrument with equity-specific attributes"""
    shares_outstanding: Optional[int] = None
    market_cap: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    
    def __post_init__(self):
        if self.instrument_type != InstrumentType.STOCK:
            raise ValueError("Stock instrument must have type STOCK")


@dataclass(frozen=True)
class Bond(ListedInstrument):
    """Bond instrument with fixed income-specific attributes"""
    coupon_frequency: int = 2  # semi-annual by default
    day_basis: DayBasis = DayBasis.THIRTY_360
    callable: bool = False
    puttable: bool = False
    call_date: Optional[date] = None
    put_date: Optional[date] = None
    
    def __post_init__(self):
        if self.instrument_type != InstrumentType.BOND:
            raise ValueError("Bond instrument must have type BOND")
        if not self.maturity_date:
            raise ValueError("maturity_date is required for bonds")
        if not self.face_value:
            raise ValueError("face_value is required for bonds")


@dataclass(frozen=True)
class InterestRateSwap(DerivativeInstrument):
    """Interest Rate Swap with IRS-specific attributes"""
    pay_leg: InterestRateLeg
    receive_leg: InterestRateLeg
    day_basis: DayBasis = DayBasis.THIRTY_360
    roll_convention: RollConvention = RollConvention.MODIFIED_FOLLOWING
    
    def __post_init__(self):
        if self.instrument_type != InstrumentType.IRS:
            raise ValueError("InterestRateSwap must have type IRS")
        if not self.pay_leg or not self.receive_leg:
            raise ValueError("pay_leg and receive_leg are required for IRS")
        if self.pay_leg.currency != self.receive_leg.currency:
            raise ValueError("pay_leg and receive_leg must have same currency")


@dataclass(frozen=True)
class CreditDefaultSwap(DerivativeInstrument):
    """Credit Default Swap with CDS-specific attributes"""
    reference_entity: str
    protection_buyer: str
    protection_seller: str
    credit_events: List[str] = field(default_factory=lambda: ["BANKRUPTCY", "FAILURE_TO_PAY", "RESTRUCTURING"])
    recovery_rate: Decimal = Decimal("0.40")  # 40% default recovery rate
    day_basis: DayBasis = DayBasis.THIRTY_360
    
    def __post_init__(self):
        if self.instrument_type != InstrumentType.CDS:
            raise ValueError("CreditDefaultSwap must have type CDS")


# Factory function to create appropriate instrument type
def create_instrument(
    instrument_type: InstrumentType,
    instrument_id: str,
    **kwargs
) -> Union[ListedInstrument, DerivativeInstrument]:
    """Factory function to create the appropriate instrument type"""
    
    if instrument_type in [InstrumentType.STOCK, InstrumentType.BOND, InstrumentType.ETF]:
        if instrument_type == InstrumentType.STOCK:
            return Stock(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
        elif instrument_type == InstrumentType.BOND:
            return Bond(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
        else:
            return ListedInstrument(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
    
    elif instrument_type in [InstrumentType.IRS, InstrumentType.CDS]:
        if instrument_type == InstrumentType.IRS:
            return InterestRateSwap(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
        elif instrument_type == InstrumentType.CDS:
            return CreditDefaultSwap(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
        else:
            return DerivativeInstrument(instrument_id=instrument_id, instrument_type=instrument_type, **kwargs)
    
    else:
        raise ValueError(f"Unsupported instrument type: {instrument_type}")


# Example usage and validation
if __name__ == "__main__":
    # Create a stock
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
    
    # Create a bond
    treasury_bond = create_instrument(
        instrument_type=InstrumentType.BOND,
        instrument_id="UST_10Y",
        ticker="UST10Y",
        name="US Treasury 10-Year Bond",
        currency="USD",
        exchange="OTC",
        isin="US912810TM64",
        cusip="912810TM6",
        face_value=Decimal("1000.00"),
        coupon_rate=Decimal("0.025"),  # 2.5%
        maturity_date=date(2033, 5, 15),
        issue_date=date(2023, 5, 15),
        issuer="US Treasury",
        country="US"
    )
    treasury_bond.validate()
    
    # Create an IRS
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
    
    print("All instruments created and validated successfully!")
