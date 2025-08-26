"""
FintechForge Data Models

This package provides comprehensive data models for trading operations,
addressing the key challenges in modeling trades and instruments.

Key Features:
- Listed vs Derivative Instrument Modeling
- Economic vs Metadata Attribute Separation
- Trade Status Change Tracking
- Organization-Specific Patterns
- Comprehensive Validation
- Audit Trail Support
"""

from .order import Order, Side as OrderSide, OrderType
from .instrument import (
    InstrumentType,
    DayBasis,
    RollConvention,
    InterestRateLeg,
    ListedInstrument,
    DerivativeInstrument,
    Stock,
    Bond,
    InterestRateSwap,
    CreditDefaultSwap,
    create_instrument
)
from .trade import (
    TradeStatus,
    TradeType,
    Side as TradeSide,
    TradeEconomics,
    TradeMetadata,
    TradeStatusChange,
    Trade,
    InvestmentManagerTrade,
    HedgeFundTrade,
    MarketMakerTrade,
    BrokerageTrade,
    StockTrade,
    BondTrade,
    IRSTrade,
    CDSTrade,
    create_trade
)

__all__ = [
    # Order models
    'Order',
    'OrderSide',
    'OrderType',
    
    # Instrument models
    'InstrumentType',
    'DayBasis',
    'RollConvention',
    'InterestRateLeg',
    'ListedInstrument',
    'DerivativeInstrument',
    'Stock',
    'Bond',
    'InterestRateSwap',
    'CreditDefaultSwap',
    'create_instrument',
    
    # Trade models
    'TradeStatus',
    'TradeType',
    'TradeSide',
    'TradeEconomics',
    'TradeMetadata',
    'TradeStatusChange',
    'Trade',
    'InvestmentManagerTrade',
    'HedgeFundTrade',
    'MarketMakerTrade',
    'BrokerageTrade',
    'StockTrade',
    'BondTrade',
    'IRSTrade',
    'CDSTrade',
    'create_trade'
]

__version__ = "1.0.0"
