#!/usr/bin/env python3
"""
Timezone Challenges in Global Trading Systems - Practical Example

This example demonstrates the critical challenges of handling trade times
across multiple timezones and jurisdictions, showing both problematic
approaches and modern solutions.
"""

from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from dataclasses import dataclass, field
from typing import Dict, Set, Any, Optional
import uuid


# ============================================================================
# PROBLEMATIC APPROACHES (DON'T DO THIS)
# ============================================================================

class LegacyTradeSystem:
    """Legacy system with poor timezone handling - DON'T USE"""
    
    def __init__(self):
        self.system_timezone = "UTC"  # Assumes single timezone
    
    def record_trade(self, trade_time: str, instrument: str, quantity: float, price: float):
        """Record trade with string-based time - PROBLEMATIC"""
        # Problem 1: String-based time storage
        self.execution_time = trade_time  # "2023-12-15 14:30:00"
        
        # Problem 2: Assumes single timezone
        self.settlement_date = self._calculate_settlement_date(trade_time)
        
        # Problem 3: No timezone information
        print(f"❌ Legacy System - Trade recorded: {trade_time}")
        print(f"   Settlement date: {self.settlement_date}")
        print(f"   Problem: No timezone context!")
    
    def _calculate_settlement_date(self, trade_time: str) -> str:
        """Calculate settlement date - PROBLEMATIC"""
        # Problem: Assumes T+2 in system timezone
        dt = datetime.strptime(trade_time, "%Y-%m-%d %H:%M:%S")
        settlement = dt + timedelta(days=2)
        return settlement.strftime("%Y-%m-%d")


class ManualTimezoneSystem:
    """System with manual timezone conversions - DON'T USE"""
    
    def __init__(self):
        self.timezone_offsets = {
            "EST": -5,
            "PST": -8,
            "GMT": 0,
            "JST": 9,
            "AEST": 10
        }
    
    def convert_timezone(self, time: datetime, from_tz: str, to_tz: str) -> datetime:
        """Manual timezone conversion - PROBLEMATIC"""
        # Problem 1: Manual offset calculations
        from_offset = self.timezone_offsets.get(from_tz, 0)
        to_offset = self.timezone_offsets.get(to_tz, 0)
        
        # Problem 2: Doesn't handle DST
        offset_diff = to_offset - from_offset
        
        # Problem 3: Simple hour addition/subtraction
        return time + timedelta(hours=offset_diff)


# ============================================================================
# MODERN SOLUTIONS (DO THIS)
# ============================================================================

@dataclass(frozen=True)
class TradeTime:
    """Immutable trade time with timezone awareness"""
    timestamp: datetime  # Always in UTC
    execution_timezone: ZoneInfo
    settlement_timezone: ZoneInfo
    
    @classmethod
    def from_local_time(cls, local_time: datetime, tz: ZoneInfo, 
                       settlement_timezone: ZoneInfo) -> 'TradeTime':
        """Create from local time with explicit timezone"""
        # Convert to UTC immediately
        utc_time = local_time.replace(tzinfo=tz).astimezone(timezone.utc)
        return cls(
            timestamp=utc_time,
            execution_timezone=tz,
            settlement_timezone=settlement_timezone
        )
    
    def get_execution_local_time(self) -> datetime:
        """Get execution time in local timezone"""
        return self.timestamp.astimezone(self.execution_timezone)
    
    def get_settlement_local_time(self) -> datetime:
        """Get settlement time in local timezone"""
        return self.timestamp.astimezone(self.settlement_timezone)
    
    def get_settlement_date(self) -> date:
        """Get settlement date in settlement timezone"""
        return self.get_settlement_local_time().date()


class BusinessCalendar:
    """Business calendar for different jurisdictions"""
    
    def __init__(self, timezone: ZoneInfo, name: str):
        self.timezone = timezone
        self.name = name
        self.holidays: Set[date] = set()
        self.weekend_days: Set[int] = {5, 6}  # Saturday, Sunday
    
    def add_holiday(self, holiday_date: date):
        """Add a holiday to the calendar"""
        self.holidays.add(holiday_date)
    
    def is_business_day(self, check_date: date) -> bool:
        """Check if date is a business day"""
        return (check_date.weekday() not in self.weekend_days and 
                check_date not in self.holidays)
    
    def next_business_day(self, from_date: date) -> date:
        """Get next business day"""
        current = from_date + timedelta(days=1)
        while not self.is_business_day(current):
            current += timedelta(days=1)
        return current
    
    def add_business_days(self, from_date: date, days: int) -> date:
        """Add business days to a date"""
        current = from_date
        remaining_days = days
        
        while remaining_days > 0:
            current = self.next_business_day(current)
            remaining_days -= 1
        
        return current


class GlobalSettlementCalculator:
    """Calculate settlement dates across timezones"""
    
    def __init__(self):
        self.calendars: Dict[str, BusinessCalendar] = {}
        self._initialize_calendars()
    
    def _initialize_calendars(self):
        """Initialize business calendars for major jurisdictions"""
        # US calendar
        us_calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        us_calendar.add_holiday(date(2023, 12, 25))  # Christmas
        us_calendar.add_holiday(date(2024, 1, 1))    # New Year
        self.calendars["US"] = us_calendar
        
        # UK calendar
        uk_calendar = BusinessCalendar(ZoneInfo("Europe/London"), "UK")
        uk_calendar.add_holiday(date(2023, 12, 25))  # Christmas
        uk_calendar.add_holiday(date(2023, 12, 26))  # Boxing Day
        self.calendars["UK"] = uk_calendar
        
        # Japan calendar
        jp_calendar = BusinessCalendar(ZoneInfo("Asia/Tokyo"), "Japan")
        jp_calendar.add_holiday(date(2023, 12, 23))  # Emperor's Birthday
        jp_calendar.add_holiday(date(2024, 1, 1))    # New Year
        self.calendars["JP"] = jp_calendar
    
    def calculate_settlement_date(self, trade_time: TradeTime, 
                                settlement_days: int) -> date:
        """Calculate settlement date considering timezone and business calendar"""
        # Get settlement timezone calendar
        calendar_key = str(trade_time.settlement_timezone).split('/')[-1]
        calendar = self.calendars.get(calendar_key, 
                                    BusinessCalendar(trade_time.settlement_timezone, calendar_key))
        
        # Get trade date in settlement timezone
        trade_date = trade_time.get_settlement_local_time().date()
        
        # Add business days
        return calendar.add_business_days(trade_date, settlement_days)


@dataclass
class TradeEvent:
    """Event with timezone-aware timestamp"""
    event_id: str
    event_type: str
    trade_id: str
    timestamp: datetime  # Always UTC
    source_timezone: ZoneInfo
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat(),
            "source_timezone": str(self.source_timezone),
            "data": self.data
        }


class ModernTradeSystem:
    """Modern system with proper timezone handling"""
    
    def __init__(self):
        self.settlement_calculator = GlobalSettlementCalculator()
        self.trades: Dict[str, TradeTime] = {}
    
    def record_trade(self, local_time: datetime, execution_timezone: ZoneInfo,
                    settlement_timezone: ZoneInfo, instrument: str, 
                    quantity: float, price: float) -> str:
        """Record trade with proper timezone handling"""
        
        # Create timezone-aware trade time
        trade_time = TradeTime.from_local_time(
            local_time=local_time,
            tz=execution_timezone,
            settlement_timezone=settlement_timezone
        )
        
        # Calculate settlement date
        settlement_date = self.settlement_calculator.calculate_settlement_date(
            trade_time, settlement_days=2
        )
        
        # Generate trade ID
        trade_id = str(uuid.uuid4())[:8]
        self.trades[trade_id] = trade_time
        
        print(f"✅ Modern System - Trade {trade_id} recorded:")
        print(f"   Execution: {trade_time.get_execution_local_time()} ({execution_timezone})")
        print(f"   UTC: {trade_time.timestamp}")
        print(f"   Settlement: {settlement_date} ({settlement_timezone})")
        print(f"   Instrument: {instrument}, Qty: {quantity}, Price: {price}")
        
        return trade_id
    
    def get_trade_summary(self, trade_id: str) -> Dict[str, Any]:
        """Get comprehensive trade summary with timezone information"""
        if trade_id not in self.trades:
            raise ValueError(f"Trade {trade_id} not found")
        
        trade_time = self.trades[trade_id]
        
        return {
            "trade_id": trade_id,
            "utc_timestamp": trade_time.timestamp.isoformat(),
            "execution_local_time": trade_time.get_execution_local_time().isoformat(),
            "settlement_local_time": trade_time.get_settlement_local_time().isoformat(),
            "execution_timezone": str(trade_time.execution_timezone),
            "settlement_timezone": str(trade_time.settlement_timezone),
            "settlement_date": trade_time.get_settlement_date().isoformat(),
            "utc_offset_execution": trade_time.get_execution_local_time().utcoffset().total_seconds() / 3600,
            "utc_offset_settlement": trade_time.get_settlement_local_time().utcoffset().total_seconds() / 3600
        }


# ============================================================================
# DEMONSTRATION SCENARIOS
# ============================================================================

def demonstrate_problematic_approaches():
    """Demonstrate problematic timezone handling approaches"""
    print("=" * 80)
    print("PROBLEMATIC APPROACHES (DON'T DO THIS)")
    print("=" * 80)
    
    # Scenario 1: Legacy system with string-based times
    print("\n1. Legacy System with String-Based Times:")
    legacy_system = LegacyTradeSystem()
    legacy_system.record_trade(
        trade_time="2023-12-15 23:30:00",  # London time
        instrument="AAPL",
        quantity=1000,
        price=150.00
    )
    
    # Scenario 2: Manual timezone conversion
    print("\n2. Manual Timezone Conversion:")
    manual_system = ManualTimezoneSystem()
    london_time = datetime(2023, 12, 15, 23, 30, 0)
    tokyo_time = manual_system.convert_timezone(london_time, "GMT", "JST")
    print(f"❌ Manual conversion: London {london_time} → Tokyo {tokyo_time}")
    print(f"   Problem: Doesn't handle DST, brittle to timezone changes")


def demonstrate_modern_solutions():
    """Demonstrate modern timezone handling solutions"""
    print("\n" + "=" * 80)
    print("MODERN SOLUTIONS (DO THIS)")
    print("=" * 80)
    
    modern_system = ModernTradeSystem()
    
    # Scenario 1: London trade settling in Tokyo
    print("\n1. London Trade Settling in Tokyo:")
    london_time = datetime(2023, 12, 15, 23, 30, 0)  # Friday 23:30 London
    trade_id_1 = modern_system.record_trade(
        local_time=london_time,
        execution_timezone=ZoneInfo("Europe/London"),
        settlement_timezone=ZoneInfo("Asia/Tokyo"),
        instrument="JP_EQUITY",
        quantity=1000,
        price=5000.00
    )
    
    # Scenario 2: New York trade settling in London
    print("\n2. New York Trade Settling in London:")
    ny_time = datetime(2023, 12, 15, 15, 0, 0)  # Friday 15:00 NY
    trade_id_2 = modern_system.record_trade(
        local_time=ny_time,
        execution_timezone=ZoneInfo("America/New_York"),
        settlement_timezone=ZoneInfo("Europe/London"),
        instrument="UK_BOND",
        quantity=1000000,
        price=98.50
    )
    
    # Scenario 3: Sydney trade settling in New York
    print("\n3. Sydney Trade Settling in New York:")
    sydney_time = datetime(2023, 12, 15, 9, 0, 0)  # Friday 09:00 Sydney
    trade_id_3 = modern_system.record_trade(
        local_time=sydney_time,
        execution_timezone=ZoneInfo("Australia/Sydney"),
        settlement_timezone=ZoneInfo("America/New_York"),
        instrument="US_STOCK",
        quantity=500,
        price=200.00
    )
    
    return [trade_id_1, trade_id_2, trade_id_3]


def demonstrate_timezone_edge_cases():
    """Demonstrate timezone edge cases and challenges"""
    print("\n" + "=" * 80)
    print("TIMEZONE EDGE CASES")
    print("=" * 80)
    
    # Edge case 1: Daylight Saving Time transition
    print("\n1. Daylight Saving Time Transition:")
    # Spring forward in US (March 12, 2023)
    spring_forward = datetime(2023, 3, 12, 2, 30, 0)  # Ambiguous time
    print(f"❌ Ambiguous time during DST transition: {spring_forward}")
    print(f"   This time doesn't exist in US Eastern Time!")
    
    # Fall back in US (November 5, 2023)
    fall_back = datetime(2023, 11, 5, 2, 30, 0)  # Duplicate time
    print(f"❌ Duplicate time during DST transition: {fall_back}")
    print(f"   This time occurs twice in US Eastern Time!")
    
    # Edge case 2: Year-end timezone differences
    print("\n2. Year-End Timezone Differences:")
    # Trade at year-end across timezones
    year_end_london = datetime(2023, 12, 31, 23, 30, 0)
    trade_time = TradeTime.from_local_time(
        local_time=year_end_london,
        tz=ZoneInfo("Europe/London"),
        settlement_timezone=ZoneInfo("Asia/Tokyo")
    )
    
    print(f"✅ London year-end: {trade_time.get_execution_local_time()}")
    print(f"   Tokyo year-end: {trade_time.get_settlement_local_time()}")
    print(f"   Settlement date: {trade_time.get_settlement_date()}")
    
    # Edge case 3: Business calendar holidays
    print("\n3. Business Calendar Holidays:")
    # Trade on Friday before Christmas
    christmas_eve = datetime(2023, 12, 22, 14, 0, 0)  # Friday 14:00 London
    trade_time = TradeTime.from_local_time(
        local_time=christmas_eve,
        tz=ZoneInfo("Europe/London"),
        settlement_timezone=ZoneInfo("Europe/London")
    )
    
    settlement_calc = GlobalSettlementCalculator()
    settlement_date = settlement_calc.calculate_settlement_date(trade_time, 2)
    
    print(f"✅ Trade date: {trade_time.get_execution_local_time().date()}")
    print(f"   Settlement date: {settlement_date}")
    print(f"   Note: Skips Christmas and Boxing Day holidays")


def demonstrate_cross_system_consistency():
    """Demonstrate cross-system timezone consistency"""
    print("\n" + "=" * 80)
    print("CROSS-SYSTEM CONSISTENCY")
    print("=" * 80)
    
    # Simulate the same trade across different systems
    trade_time = datetime(2023, 12, 15, 14, 30, 0)  # London time
    
    # Create timezone-aware trade time
    trade_time_aware = TradeTime.from_local_time(
        local_time=trade_time,
        tz=ZoneInfo("Europe/London"),
        settlement_timezone=ZoneInfo("Asia/Tokyo")
    )
    
    # Simulate different systems
    systems = {
        "Trading System (London)": ZoneInfo("Europe/London"),
        "Risk System (New York)": ZoneInfo("America/New_York"),
        "Settlement System (Tokyo)": ZoneInfo("Asia/Tokyo"),
        "Accounting System (UTC)": ZoneInfo("UTC")
    }
    
    print("Same trade across different systems:")
    print(f"   UTC Timestamp: {trade_time_aware.timestamp}")
    
    for system_name, system_timezone in systems.items():
        local_time = trade_time_aware.timestamp.astimezone(system_timezone)
        print(f"   {system_name}: {local_time}")
    
    # Verify consistency
    print(f"\n✅ Consistency Check:")
    print(f"   All systems show the same UTC timestamp")
    print(f"   Local times are correctly converted")
    print(f"   Settlement date: {trade_time_aware.get_settlement_date()}")


def main():
    """Run all demonstrations"""
    print("TIMEZONE CHALLENGES IN GLOBAL TRADING SYSTEMS")
    print("Demonstrating problematic approaches and modern solutions")
    print("=" * 80)
    
    # Demonstrate problematic approaches
    demonstrate_problematic_approaches()
    
    # Demonstrate modern solutions
    trade_ids = demonstrate_modern_solutions()
    
    # Demonstrate edge cases
    demonstrate_timezone_edge_cases()
    
    # Demonstrate cross-system consistency
    demonstrate_cross_system_consistency()
    
    # Show trade summaries
    print("\n" + "=" * 80)
    print("TRADE SUMMARIES")
    print("=" * 80)
    
    modern_system = ModernTradeSystem()
    for trade_id in trade_ids:
        summary = modern_system.get_trade_summary(trade_id)
        print(f"\nTrade {trade_id}:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("1. Always store UTC timestamps with timezone metadata")
    print("2. Use proper timezone libraries (zoneinfo/pytz)")
    print("3. Integrate business calendars for settlement calculations")
    print("4. Handle DST transitions and edge cases")
    print("5. Maintain consistency across all systems")
    print("6. Test with multiple timezones and jurisdictions")


if __name__ == "__main__":
    main()
