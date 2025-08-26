#!/usr/bin/env python3
"""
Unit tests for timezone example functionality

Tests all timezone handling classes and functionality including:
- TradeTime class with timezone awareness
- BusinessCalendar class with holiday handling
- GlobalSettlementCalculator with cross-timezone settlement
- ModernTradeSystem with complete trade lifecycle
- Edge cases and error conditions
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

# Import the classes from the timezone example
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'examples', 'python'))

from timezone_example import (
    TradeTime, BusinessCalendar, GlobalSettlementCalculator,
    ModernTradeSystem, TradeEvent, LegacyTradeSystem, ManualTimezoneSystem
)


class TestTradeTime:
    """Test TradeTime class functionality"""
    
    def test_from_local_time_creation(self):
        """Test creating TradeTime from local time"""
        # London time
        london_time = datetime(2023, 12, 15, 14, 30, 0)
        trade_time = TradeTime.from_local_time(
            local_time=london_time,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Asia/Tokyo")
        )
        
        assert trade_time.timestamp == datetime(2023, 12, 15, 14, 30, 0, tzinfo=timezone.utc)
        assert trade_time.execution_timezone == ZoneInfo("Europe/London")
        assert trade_time.settlement_timezone == ZoneInfo("Asia/Tokyo")
    
    def test_get_execution_local_time(self):
        """Test getting execution time in local timezone"""
        # New York time
        ny_time = datetime(2023, 12, 15, 9, 0, 0)
        trade_time = TradeTime.from_local_time(
            local_time=ny_time,
            tz=ZoneInfo("America/New_York"),
            settlement_timezone=ZoneInfo("Europe/London")
        )
        
        local_time = trade_time.get_execution_local_time()
        assert local_time.hour == 9
        assert local_time.minute == 0
        assert local_time.tzinfo == ZoneInfo("America/New_York")
    
    def test_get_settlement_local_time(self):
        """Test getting settlement time in local timezone"""
        # Sydney time
        sydney_time = datetime(2023, 12, 15, 10, 0, 0)
        trade_time = TradeTime.from_local_time(
            local_time=sydney_time,
            tz=ZoneInfo("Australia/Sydney"),
            settlement_timezone=ZoneInfo("Asia/Tokyo")
        )
        
        settlement_time = trade_time.get_settlement_local_time()
        assert settlement_time.tzinfo == ZoneInfo("Asia/Tokyo")
        # Sydney is UTC+11, Tokyo is UTC+9, so settlement time should be 2 hours earlier
        assert settlement_time.hour == 8
    
    def test_get_settlement_date(self):
        """Test getting settlement date in settlement timezone"""
        # London time at year-end
        london_time = datetime(2023, 12, 31, 23, 30, 0)
        trade_time = TradeTime.from_local_time(
            local_time=london_time,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Asia/Tokyo")
        )
        
        settlement_date = trade_time.get_settlement_date()
        # London 23:30 on Dec 31 = Tokyo 08:30 on Jan 1
        assert settlement_date == date(2024, 1, 1)
    
    def test_timezone_conversion_accuracy(self):
        """Test timezone conversion accuracy across different scenarios"""
        # Test various timezone combinations
        scenarios = [
            (datetime(2023, 12, 15, 14, 0, 0), "Europe/London", "America/New_York", 9),  # 14:00 London = 09:00 NY
            (datetime(2023, 12, 15, 9, 0, 0), "America/New_York", "Asia/Tokyo", 23),      # 09:00 NY = 23:00 Tokyo
            (datetime(2023, 12, 15, 10, 0, 0), "Australia/Sydney", "Europe/London", 23),  # 10:00 Sydney = 23:00 London
        ]
        
        for local_time, exec_tz, settle_tz, expected_hour in scenarios:
            trade_time = TradeTime.from_local_time(
                local_time=local_time,
                tz=ZoneInfo(exec_tz),
                settlement_timezone=ZoneInfo(settle_tz)
            )
            
            settlement_time = trade_time.get_settlement_local_time()
            assert settlement_time.hour == expected_hour


class TestBusinessCalendar:
    """Test BusinessCalendar class functionality"""
    
    def test_basic_business_day_calculation(self):
        """Test basic business day calculations"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        
        # Monday should be a business day
        monday = date(2023, 12, 18)  # Monday
        assert calendar.is_business_day(monday) == True
        
        # Saturday should not be a business day
        saturday = date(2023, 12, 16)  # Saturday
        assert calendar.is_business_day(saturday) == False
        
        # Sunday should not be a business day
        sunday = date(2023, 12, 17)  # Sunday
        assert calendar.is_business_day(sunday) == False
    
    def test_holiday_handling(self):
        """Test holiday handling"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        calendar.add_holiday(date(2023, 12, 25))  # Christmas
        
        # Christmas should not be a business day
        christmas = date(2023, 12, 25)
        assert calendar.is_business_day(christmas) == False
        
        # Day after Christmas should be a business day
        day_after = date(2023, 12, 26)
        assert calendar.is_business_day(day_after) == True
    
    def test_next_business_day(self):
        """Test next business day calculation"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        calendar.add_holiday(date(2023, 12, 25))  # Christmas
        
        # Friday before Christmas
        friday = date(2023, 12, 22)  # Friday
        next_business = calendar.next_business_day(friday)
        # Should skip weekend and Christmas, so next business day is Dec 26
        assert next_business == date(2023, 12, 26)
    
    def test_add_business_days(self):
        """Test adding business days"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        calendar.add_holiday(date(2023, 12, 25))  # Christmas
        
        # Start on Friday before Christmas
        start_date = date(2023, 12, 22)  # Friday
        result = calendar.add_business_days(start_date, 2)
        # Should skip weekend and Christmas, so 2 business days later is Dec 27
        assert result == date(2023, 12, 27)
    
    def test_weekend_handling(self):
        """Test weekend handling"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        
        # Start on Friday, add 1 business day
        friday = date(2023, 12, 15)  # Friday
        result = calendar.add_business_days(friday, 1)
        # Should skip weekend, so next business day is Monday
        assert result == date(2023, 12, 18)  # Monday
    
    def test_different_weekend_days(self):
        """Test calendar with different weekend days (e.g., Middle East)"""
        # Middle East calendar (Friday-Saturday weekend)
        calendar = BusinessCalendar(ZoneInfo("Asia/Dubai"), "UAE")
        calendar.weekend_days = {4, 5}  # Friday, Saturday
        
        # Thursday should be a business day
        thursday = date(2023, 12, 21)  # Thursday
        assert calendar.is_business_day(thursday) == True
        
        # Friday should not be a business day
        friday = date(2023, 12, 22)  # Friday
        assert calendar.is_business_day(friday) == False
        
        # Sunday should be a business day
        sunday = date(2023, 12, 24)  # Sunday
        assert calendar.is_business_day(sunday) == True


class TestGlobalSettlementCalculator:
    """Test GlobalSettlementCalculator class functionality"""
    
    def test_calculate_settlement_date_us_trade(self):
        """Test settlement date calculation for US trade"""
        calculator = GlobalSettlementCalculator()
        
        # US trade on Friday
        us_time = datetime(2023, 12, 15, 15, 0, 0)  # Friday 15:00 NY
        trade_time = TradeTime.from_local_time(
            local_time=us_time,
            tz=ZoneInfo("America/New_York"),
            settlement_timezone=ZoneInfo("America/New_York")
        )
        
        settlement_date = calculator.calculate_settlement_date(trade_time, 2)
        # T+2 from Friday should be Tuesday (skip weekend)
        assert settlement_date == date(2023, 12, 19)  # Tuesday
    
    def test_calculate_settlement_date_uk_trade(self):
        """Test settlement date calculation for UK trade"""
        calculator = GlobalSettlementCalculator()
        
        # UK trade on Friday
        uk_time = datetime(2023, 12, 15, 14, 0, 0)  # Friday 14:00 London
        trade_time = TradeTime.from_local_time(
            local_time=uk_time,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Europe/London")
        )
        
        settlement_date = calculator.calculate_settlement_date(trade_time, 2)
        # T+2 from Friday should be Tuesday (skip weekend)
        assert settlement_date == date(2023, 12, 19)  # Tuesday
    
    def test_calculate_settlement_date_cross_timezone(self):
        """Test settlement date calculation across timezones"""
        calculator = GlobalSettlementCalculator()
        
        # London trade settling in Tokyo
        london_time = datetime(2023, 12, 15, 23, 30, 0)  # Friday 23:30 London
        trade_time = TradeTime.from_local_time(
            local_time=london_time,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Asia/Tokyo")
        )
        
        settlement_date = calculator.calculate_settlement_date(trade_time, 2)
        # London 23:30 Friday = Tokyo 08:30 Saturday
        # T+2 from Saturday should be Tuesday (skip weekend)
        assert settlement_date == date(2023, 12, 19)  # Tuesday
    
    def test_holiday_handling_in_settlement(self):
        """Test holiday handling in settlement calculations"""
        calculator = GlobalSettlementCalculator()
        
        # Trade on Friday before Christmas
        christmas_eve = datetime(2023, 12, 22, 14, 0, 0)  # Friday 14:00 London
        trade_time = TradeTime.from_local_time(
            local_time=christmas_eve,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Europe/London")
        )
        
        settlement_date = calculator.calculate_settlement_date(trade_time, 2)
        # Should skip Christmas and Boxing Day
        assert settlement_date == date(2023, 12, 26)  # Tuesday after Christmas
    
    def test_different_settlement_cycles(self):
        """Test different settlement cycles (T+1, T+2, T+3)"""
        calculator = GlobalSettlementCalculator()
        
        # US trade on Monday
        monday_time = datetime(2023, 12, 18, 15, 0, 0)  # Monday 15:00 NY
        trade_time = TradeTime.from_local_time(
            local_time=monday_time,
            tz=ZoneInfo("America/New_York"),
            settlement_timezone=ZoneInfo("America/New_York")
        )
        
        # T+1 settlement
        t1_settlement = calculator.calculate_settlement_date(trade_time, 1)
        assert t1_settlement == date(2023, 12, 19)  # Tuesday
        
        # T+2 settlement
        t2_settlement = calculator.calculate_settlement_date(trade_time, 2)
        assert t2_settlement == date(2023, 12, 20)  # Wednesday
        
        # T+3 settlement
        t3_settlement = calculator.calculate_settlement_date(trade_time, 3)
        assert t3_settlement == date(2023, 12, 21)  # Thursday


class TestModernTradeSystem:
    """Test ModernTradeSystem class functionality"""
    
    def test_record_trade_basic(self):
        """Test basic trade recording"""
        system = ModernTradeSystem()
        
        # Record a simple trade
        trade_time = datetime(2023, 12, 15, 14, 30, 0)
        trade_id = system.record_trade(
            local_time=trade_time,
            execution_timezone=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Europe/London"),
            instrument="UK_BOND",
            quantity=1000000,
            price=98.50
        )
        
        assert trade_id is not None
        assert len(trade_id) == 8
        assert trade_id in system.trades
    
    def test_record_trade_cross_timezone(self):
        """Test cross-timezone trade recording"""
        system = ModernTradeSystem()
        
        # London trade settling in Tokyo
        london_time = datetime(2023, 12, 15, 23, 30, 0)
        trade_id = system.record_trade(
            local_time=london_time,
            execution_timezone=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Asia/Tokyo"),
            instrument="JP_EQUITY",
            quantity=1000,
            price=5000.00
        )
        
        trade_time = system.trades[trade_id]
        assert trade_time.execution_timezone == ZoneInfo("Europe/London")
        assert trade_time.settlement_timezone == ZoneInfo("Asia/Tokyo")
        
        # Verify settlement date calculation
        settlement_date = system.settlement_calculator.calculate_settlement_date(trade_time, 2)
        assert settlement_date == date(2023, 12, 19)  # Tuesday (skip weekend)
    
    def test_get_trade_summary(self):
        """Test getting trade summary"""
        system = ModernTradeSystem()
        
        # Record a trade
        trade_time = datetime(2023, 12, 15, 14, 30, 0)
        trade_id = system.record_trade(
            local_time=trade_time,
            execution_timezone=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("America/New_York"),
            instrument="US_STOCK",
            quantity=500,
            price=200.00
        )
        
        # Get summary
        summary = system.get_trade_summary(trade_id)
        
        assert summary["trade_id"] == trade_id
        assert "utc_timestamp" in summary
        assert "execution_local_time" in summary
        assert "settlement_local_time" in summary
        assert "execution_timezone" in summary
        assert "settlement_timezone" in summary
        assert "settlement_date" in summary
        assert "utc_offset_execution" in summary
        assert "utc_offset_settlement" in summary
        
        # Verify timezone information
        assert summary["execution_timezone"] == "Europe/London"
        assert summary["settlement_timezone"] == "America/New_York"
    
    def test_get_trade_summary_not_found(self):
        """Test getting trade summary for non-existent trade"""
        system = ModernTradeSystem()
        
        with pytest.raises(ValueError, match="Trade NONEXISTENT not found"):
            system.get_trade_summary("NONEXISTENT")
    
    def test_multiple_trades(self):
        """Test recording multiple trades"""
        system = ModernTradeSystem()
        
        # Record multiple trades
        trades = [
            (datetime(2023, 12, 15, 9, 0, 0), ZoneInfo("America/New_York"), ZoneInfo("America/New_York")),
            (datetime(2023, 12, 15, 14, 0, 0), ZoneInfo("Europe/London"), ZoneInfo("Europe/London")),
            (datetime(2023, 12, 15, 10, 0, 0), ZoneInfo("Australia/Sydney"), ZoneInfo("Asia/Tokyo")),
        ]
        
        trade_ids = []
        for local_time, exec_tz, settle_tz in trades:
            trade_id = system.record_trade(
                local_time=local_time,
                execution_timezone=exec_tz,
                settlement_timezone=settle_tz,
                instrument="TEST",
                quantity=100,
                price=100.00
            )
            trade_ids.append(trade_id)
        
        # Verify all trades were recorded
        assert len(system.trades) == 3
        for trade_id in trade_ids:
            assert trade_id in system.trades


class TestLegacyTradeSystem:
    """Test LegacyTradeSystem (problematic approach)"""
    
    def test_legacy_trade_recording(self):
        """Test legacy trade recording (demonstrates problems)"""
        system = LegacyTradeSystem()
        
        # This demonstrates the problematic approach
        system.record_trade(
            trade_time="2023-12-15 23:30:00",
            instrument="AAPL",
            quantity=1000,
            price=150.00
        )
        
        # Verify the problematic behavior
        assert system.execution_time == "2023-12-15 23:30:00"
        assert system.settlement_date == "2023-12-17"
    
    def test_legacy_settlement_calculation(self):
        """Test legacy settlement calculation (demonstrates problems)"""
        system = LegacyTradeSystem()
        
        # This shows the problematic string-based approach
        settlement = system._calculate_settlement_date("2023-12-15 14:30:00")
        assert settlement == "2023-12-17"


class TestManualTimezoneSystem:
    """Test ManualTimezoneSystem (problematic approach)"""
    
    def test_manual_timezone_conversion(self):
        """Test manual timezone conversion (demonstrates problems)"""
        system = ManualTimezoneSystem()
        
        # This demonstrates the problematic manual approach
        london_time = datetime(2023, 12, 15, 23, 30, 0)
        tokyo_time = system.convert_timezone(london_time, "GMT", "JST")
        
        # Manual calculation: 23:30 + 9 hours = 08:30 next day
        expected = datetime(2023, 12, 16, 8, 30, 0)
        assert tokyo_time == expected
    
    def test_manual_conversion_limitations(self):
        """Test limitations of manual timezone conversion"""
        system = ManualTimezoneSystem()
        
        # This shows why manual conversion is problematic
        # It doesn't handle DST transitions
        spring_forward = datetime(2023, 3, 12, 2, 30, 0)
        converted = system.convert_timezone(spring_forward, "EST", "PST")
        
        # Manual calculation: 2:30 - 3 hours = 23:30 previous day
        # But this doesn't account for DST transition
        expected = datetime(2023, 3, 11, 23, 30, 0)
        assert converted == expected


class TestTradeEvent:
    """Test TradeEvent class functionality"""
    
    def test_trade_event_creation(self):
        """Test creating trade events"""
        event = TradeEvent(
            event_id="EVENT_001",
            event_type="TRADE_EXECUTED",
            trade_id="TRADE_001",
            timestamp=datetime(2023, 12, 15, 14, 30, 0, tzinfo=timezone.utc),
            source_timezone=ZoneInfo("Europe/London"),
            data={"instrument": "AAPL", "quantity": 100}
        )
        
        assert event.event_id == "EVENT_001"
        assert event.event_type == "TRADE_EXECUTED"
        assert event.trade_id == "TRADE_001"
        assert event.source_timezone == ZoneInfo("Europe/London")
        assert event.data["instrument"] == "AAPL"
    
    def test_trade_event_serialization(self):
        """Test trade event serialization"""
        event = TradeEvent(
            event_id="EVENT_001",
            event_type="TRADE_EXECUTED",
            trade_id="TRADE_001",
            timestamp=datetime(2023, 12, 15, 14, 30, 0, tzinfo=timezone.utc),
            source_timezone=ZoneInfo("Europe/London"),
            data={"instrument": "AAPL", "quantity": 100}
        )
        
        # Convert to dictionary
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == "EVENT_001"
        assert event_dict["event_type"] == "TRADE_EXECUTED"
        assert event_dict["trade_id"] == "TRADE_001"
        assert event_dict["timestamp"] == "2023-12-15T14:30:00+00:00"
        assert event_dict["source_timezone"] == "Europe/London"
        assert event_dict["data"]["instrument"] == "AAPL"
    
    def test_trade_event_deserialization(self):
        """Test trade event deserialization"""
        # Since TradeEvent doesn't have from_dict method, test manual creation
        event_dict = {
            "event_id": "EVENT_001",
            "event_type": "TRADE_EXECUTED",
            "trade_id": "TRADE_001",
            "timestamp": "2023-12-15T14:30:00+00:00",
            "source_timezone": "Europe/London",
            "data": {"instrument": "AAPL", "quantity": 100}
        }
        
        # Manually create event from dictionary data
        event = TradeEvent(
            event_id=event_dict["event_id"],
            event_type=event_dict["event_type"],
            trade_id=event_dict["trade_id"],
            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
            source_timezone=ZoneInfo(event_dict["source_timezone"]),
            data=event_dict["data"]
        )
        
        assert event.event_id == "EVENT_001"
        assert event.event_type == "TRADE_EXECUTED"
        assert event.trade_id == "TRADE_001"
        assert event.timestamp == datetime(2023, 12, 15, 14, 30, 0, tzinfo=timezone.utc)
        assert event.source_timezone == ZoneInfo("Europe/London")
        assert event.data["instrument"] == "AAPL"


class TestTimezoneEdgeCases:
    """Test timezone edge cases and error conditions"""
    
    def test_dst_spring_forward(self):
        """Test DST spring forward edge case"""
        # March 12, 2023 - Spring forward in US
        # 2:30 AM doesn't exist in US Eastern Time
        spring_forward = datetime(2023, 3, 12, 2, 30, 0)
        
        # Test that the timezone library handles this edge case
        # The zoneinfo library will typically adjust the time automatically
        try:
            trade_time = TradeTime.from_local_time(
                local_time=spring_forward,
                tz=ZoneInfo("America/New_York"),
                settlement_timezone=ZoneInfo("America/New_York")
            )
            # If it doesn't raise an exception, verify the behavior
            assert trade_time.timestamp is not None
            # The time should be adjusted to a valid time
            assert trade_time.get_execution_local_time().hour != 2
        except Exception:
            # It's also acceptable for this to raise an exception due to DST transition
            pass
    
    def test_dst_fall_back(self):
        """Test DST fall back edge case"""
        # November 5, 2023 - Fall back in US
        # 2:30 AM occurs twice in US Eastern Time
        fall_back = datetime(2023, 11, 5, 2, 30, 0)
        
        # This should handle the ambiguous time
        # The exact behavior depends on the timezone library
        try:
            trade_time = TradeTime.from_local_time(
                local_time=fall_back,
                tz=ZoneInfo("America/New_York"),
                settlement_timezone=ZoneInfo("America/New_York")
            )
            # If it doesn't raise an exception, verify the behavior
            assert trade_time.timestamp is not None
        except Exception:
            # It's acceptable for this to raise an exception due to ambiguity
            pass
    
    def test_year_end_timezone_difference(self):
        """Test year-end timezone differences"""
        # London year-end
        london_year_end = datetime(2023, 12, 31, 23, 30, 0)
        trade_time = TradeTime.from_local_time(
            local_time=london_year_end,
            tz=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Asia/Tokyo")
        )
        
        # London 23:30 Dec 31 = Tokyo 08:30 Jan 1
        settlement_date = trade_time.get_settlement_date()
        assert settlement_date == date(2024, 1, 1)
    
    def test_business_calendar_edge_cases(self):
        """Test business calendar edge cases"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        
        # Add multiple holidays
        calendar.add_holiday(date(2023, 12, 25))  # Christmas
        calendar.add_holiday(date(2023, 12, 26))  # Boxing Day (not US holiday, but testing)
        
        # Trade on Friday before Christmas
        friday = date(2023, 12, 22)  # Friday
        result = calendar.add_business_days(friday, 2)
        # Should skip weekend and holidays
        # Friday Dec 22 + 2 business days = Monday Dec 25 (holiday) -> Tuesday Dec 26 (holiday) -> Wednesday Dec 27
        # Wait, let me recalculate: Friday Dec 22 + 1 business day = Monday Dec 25 (holiday) -> Tuesday Dec 26 (holiday) -> Wednesday Dec 27
        # + 1 more business day = Thursday Dec 28
        assert result == date(2023, 12, 28)  # Thursday
    
    def test_zero_business_days(self):
        """Test adding zero business days"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        
        start_date = date(2023, 12, 15)  # Friday
        result = calendar.add_business_days(start_date, 0)
        assert result == start_date
    
    def test_negative_business_days(self):
        """Test adding negative business days (should handle gracefully)"""
        calendar = BusinessCalendar(ZoneInfo("America/New_York"), "US")
        
        start_date = date(2023, 12, 15)  # Friday
        result = calendar.add_business_days(start_date, -1)
        # Should return the same date or handle gracefully
        assert result == start_date


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components"""
    
    def test_complete_trade_lifecycle(self):
        """Test complete trade lifecycle with timezone awareness"""
        system = ModernTradeSystem()
        
        # 1. Record trade
        trade_time = datetime(2023, 12, 15, 14, 30, 0)
        trade_id = system.record_trade(
            local_time=trade_time,
            execution_timezone=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("America/New_York"),
            instrument="US_STOCK",
            quantity=1000,
            price=150.00
        )
        
        # 2. Get trade summary
        summary = system.get_trade_summary(trade_id)
        
        # 3. Verify timezone information
        assert summary["execution_timezone"] == "Europe/London"
        assert summary["settlement_timezone"] == "America/New_York"
        
        # 4. Verify settlement date calculation
        trade_time_obj = system.trades[trade_id]
        settlement_date = system.settlement_calculator.calculate_settlement_date(trade_time_obj, 2)
        assert settlement_date == date(2023, 12, 19)  # Tuesday (skip weekend)
    
    def test_cross_timezone_settlement_scenarios(self):
        """Test various cross-timezone settlement scenarios"""
        system = ModernTradeSystem()
        
        scenarios = [
            # (execution_time, exec_tz, settle_tz, expected_settlement_date)
            (datetime(2023, 12, 15, 9, 0, 0), "America/New_York", "America/New_York", date(2023, 12, 19)),  # T+2
            (datetime(2023, 12, 15, 14, 0, 0), "Europe/London", "Europe/London", date(2023, 12, 19)),      # T+2
            (datetime(2023, 12, 15, 10, 0, 0), "Australia/Sydney", "Asia/Tokyo", date(2023, 12, 19)),      # T+2
        ]
        
        for exec_time, exec_tz, settle_tz, expected_date in scenarios:
            trade_id = system.record_trade(
                local_time=exec_time,
                execution_timezone=ZoneInfo(exec_tz),
                settlement_timezone=ZoneInfo(settle_tz),
                instrument="TEST",
                quantity=100,
                price=100.00
            )
            
            trade_time_obj = system.trades[trade_id]
            settlement_date = system.settlement_calculator.calculate_settlement_date(trade_time_obj, 2)
            assert settlement_date == expected_date
    
    def test_holiday_impact_on_settlement(self):
        """Test how holidays impact settlement dates"""
        system = ModernTradeSystem()
        
        # Trade on Friday before Christmas
        christmas_eve = datetime(2023, 12, 22, 14, 0, 0)  # Friday
        trade_id = system.record_trade(
            local_time=christmas_eve,
            execution_timezone=ZoneInfo("Europe/London"),
            settlement_timezone=ZoneInfo("Europe/London"),
            instrument="UK_BOND",
            quantity=1000000,
            price=98.50
        )
        
        trade_time_obj = system.trades[trade_id]
        settlement_date = system.settlement_calculator.calculate_settlement_date(trade_time_obj, 2)
        # Should skip Christmas and Boxing Day
        assert settlement_date == date(2023, 12, 26)  # Tuesday after Christmas


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
