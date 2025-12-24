from datetime import datetime, timezone
from enum import Enum


class DemandLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


def inventory_multiplier(remaining_seats: int, total_seats: int) -> float:
    if total_seats == 0:
        return 1.0
    remaining_pct = remaining_seats / total_seats

    if remaining_pct > 0.7:
        return 0.9
    elif remaining_pct > 0.4:
        return 1.0
    elif remaining_pct > 0.2:
        return 1.1
    else:
        return 1.25


def time_multiplier(departure_time: datetime, now: datetime | None = None) -> float:
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Ensure both datetimes are comparable (both naive or both aware)
    if departure_time.tzinfo is None and now.tzinfo is not None:
        # Make now naive to match departure_time
        now = now.replace(tzinfo=None)
    elif departure_time.tzinfo is not None and now.tzinfo is None:
        # Make departure_time naive (shouldn't happen in practice)
        departure_time = departure_time.replace(tzinfo=None)
    
    hours = (departure_time - now).total_seconds() / 3600

    if hours > 720:      # > 30 days
        return 1.0
    elif hours > 168:    # 7–30 days
        return 1.05
    elif hours > 48:     # 2–7 days
        return 1.15
    else:                # < 48 hours
        return 1.30


def demand_multiplier(demand_level: DemandLevel) -> float:
    return {
        DemandLevel.LOW: 0.95,
        DemandLevel.MEDIUM: 1.0,
        DemandLevel.HIGH: 1.10,
        DemandLevel.EXTREME: 1.25,
    }[demand_level]


def tier_multiplier(tier: str) -> float:
    mapping = {
        "ECONOMY": 1.0,
        "ECONOMY_FLEX": 1.2,
        "BUSINESS": 1.8,
        "FIRST": 2.5,
    }
    return mapping.get(tier.upper(), 1.0)


def compute_dynamic_price(
    base_fare: float,
    departure_time: datetime,
    total_seats: int,
    booked_seats: int,
    demand_level: str | DemandLevel = DemandLevel.MEDIUM,
    tier: str = "ECONOMY",
    now: datetime | None = None,
) -> float:
    """
    Compute dynamic price based on multiple factors.
    
    Args:
        base_fare: Base price for the flight
        departure_time: Scheduled departure datetime
        total_seats: Total seat capacity
        booked_seats: Number of seats already booked
        demand_level: Current demand level (low/medium/high/extreme)
        tier: Fare tier (ECONOMY/ECONOMY_FLEX/BUSINESS/FIRST)
        now: Current time (defaults to utcnow)
    
    Returns:
        Dynamic price as float rounded to 2 decimals
        
    Raises:
        ValueError: If base_fare is negative or seats are invalid
    """
    # Validation
    if base_fare < 0:
        raise ValueError("base_fare must be non-negative")
    if total_seats < 0:
        raise ValueError("total_seats must be non-negative")
    if booked_seats < 0:
        raise ValueError("booked_seats must be non-negative")
    if booked_seats > total_seats:
        raise ValueError("booked_seats cannot exceed total_seats")
    
    # Edge case: no seats or flight full
    if total_seats == 0:
        return round(base_fare, 2)
    
    remaining_seats = max(total_seats - booked_seats, 0)

    # normalize demand_level
    if isinstance(demand_level, str):
        try:
            dlevel = DemandLevel(demand_level.lower())
        except Exception:
            dlevel = DemandLevel.MEDIUM
    else:
        dlevel = demand_level

    inv_mult = inventory_multiplier(remaining_seats, total_seats)
    t_mult = time_multiplier(departure_time, now=now)
    d_mult = demand_multiplier(dlevel)
    tr_mult = tier_multiplier(tier)

    price = base_fare * inv_mult * t_mult * d_mult * tr_mult
    
    # Ensure price doesn't exceed reasonable bounds (e.g., 10x base for extreme cases)
    max_price = base_fare * 10.0
    price = min(price, max_price)
    
    return round(price, 2)
