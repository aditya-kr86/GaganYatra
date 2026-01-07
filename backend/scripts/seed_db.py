"""Seed script for FlightBooker backend.

This script is idempotent: running it multiple times won't create duplicate
airlines/airports/aircrafts or flights with the same flight_number + departure_time.

PERFORMANCE OPTIMIZED:
- Uses bulk inserts for flights and seats
- Batched commits (every 100 flights)
- Pre-cached templates to avoid repeated queries
- Minimal database round-trips
- Progress indicators for visibility

Usage:
    python scripts/seed_db.py

It will create:
- 8 Major Indian Airlines
- 25+ Indian Airports (major cities + tier-2)
- 10+ Aircraft models with realistic configurations
- Aircraft seat templates with proper seat numbering (1A, 1B, etc.)
- 500+ flights across the next 30 days with realistic schedules
- Realistic pricing based on route distance and demand

After running, start the server and call `/flights/search` to see dynamic prices.
"""
from datetime import datetime, timedelta, timezone
import random
import os
import sys
import time

# Ensure the repository `backend` folder is on sys.path so `import app` works
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.config import SessionLocal, Base, engine
from app.models.airline import Airline
from app.models.airport import Airport
from app.models.aircraft import Aircraft
from app.models.aircraft_seat_template import AircraftSeatTemplate
from app.models.flight import Flight
from app.models.seat import Seat

# SQLAlchemy for bulk operations
from sqlalchemy.orm import Session
from sqlalchemy import text


# ============================================================================
# REALISTIC INDIAN AVIATION DATA
# ============================================================================

AIRLINES_DATA = [
    # (Name, IATA Code)
    ("IndiGo", "6E"),
    ("Air India", "AI"),
    ("SpiceJet", "SG"),
    ("Vistara", "UK"),
    ("Go First", "G8"),
    ("AirAsia India", "I5"),
    ("Akasa Air", "QP"),
    ("Air India Express", "IX"),
]

AIRPORTS_DATA = [
    # (IATA Code, Name, City, Country)
    # Metro Cities
    ("DEL", "Indira Gandhi International Airport", "New Delhi", "India"),
    ("BOM", "Chhatrapati Shivaji Maharaj International Airport", "Mumbai", "India"),
    ("BLR", "Kempegowda International Airport", "Bengaluru", "India"),
    ("MAA", "Chennai International Airport", "Chennai", "India"),
    ("CCU", "Netaji Subhas Chandra Bose International Airport", "Kolkata", "India"),
    ("HYD", "Rajiv Gandhi International Airport", "Hyderabad", "India"),
    # Major Cities
    ("AMD", "Sardar Vallabhbhai Patel International Airport", "Ahmedabad", "India"),
    ("PNQ", "Pune Airport", "Pune", "India"),
    ("GOI", "Goa International Airport", "Goa", "India"),
    ("COK", "Cochin International Airport", "Kochi", "India"),
    ("JAI", "Jaipur International Airport", "Jaipur", "India"),
    ("LKO", "Chaudhary Charan Singh International Airport", "Lucknow", "India"),
    ("GAU", "Lokpriya Gopinath Bordoloi International Airport", "Guwahati", "India"),
    ("IXC", "Chandigarh International Airport", "Chandigarh", "India"),
    ("PAT", "Jay Prakash Narayan International Airport", "Patna", "India"),
    # Tier-2 Cities
    ("VNS", "Lal Bahadur Shastri International Airport", "Varanasi", "India"),
    ("IXB", "Bagdogra Airport", "Siliguri", "India"),
    ("TRV", "Trivandrum International Airport", "Thiruvananthapuram", "India"),
    ("IXR", "Birsa Munda Airport", "Ranchi", "India"),
    ("BBI", "Biju Patnaik International Airport", "Bhubaneswar", "India"),
    ("IDR", "Devi Ahilyabai Holkar Airport", "Indore", "India"),
    ("NAG", "Dr. Babasaheb Ambedkar International Airport", "Nagpur", "India"),
    ("SXR", "Sheikh ul-Alam International Airport", "Srinagar", "India"),
    ("IXJ", "Jammu Airport", "Jammu", "India"),
    ("ATQ", "Sri Guru Ram Dass Jee International Airport", "Amritsar", "India"),
]

AIRCRAFT_DATA = [
    # (Model, Total Capacity, Economy, Business, Premium Economy, First Class)
    ("Airbus A320neo", 180, 156, 12, 12, 0),
    ("Airbus A321neo", 220, 188, 20, 12, 0),
    ("Airbus A320ceo", 174, 150, 12, 12, 0),
    ("Boeing 737-800", 168, 144, 12, 12, 0),
    ("Boeing 737 MAX 8", 178, 154, 12, 12, 0),
    ("ATR 72-600", 70, 70, 0, 0, 0),
    ("Airbus A350-900", 300, 226, 36, 24, 14),
    ("Boeing 787-8 Dreamliner", 256, 198, 30, 18, 10),
    ("Boeing 777-300ER", 342, 256, 44, 28, 14),
    ("Airbus A330-300", 280, 212, 36, 24, 8),
]

# Route data with approximate flight duration (minutes) and base price range
# Format: (origin, destination, duration_min, duration_max, base_price_min, base_price_max)
ROUTES_DATA = [
    # Delhi Hub Routes
    ("DEL", "BOM", 120, 140, 4500, 8500),
    ("DEL", "BLR", 150, 175, 5000, 9500),
    ("DEL", "MAA", 160, 185, 5500, 10000),
    ("DEL", "CCU", 130, 155, 4000, 7500),
    ("DEL", "HYD", 130, 150, 4500, 8000),
    ("DEL", "AMD", 90, 110, 3500, 6500),
    ("DEL", "GOI", 145, 165, 5000, 9000),
    ("DEL", "JAI", 55, 70, 2500, 5000),
    ("DEL", "LKO", 75, 90, 3000, 5500),
    ("DEL", "SXR", 85, 100, 4500, 8500),
    ("DEL", "ATQ", 65, 80, 3000, 5500),
    ("DEL", "IXC", 55, 70, 2500, 4500),
    ("DEL", "GAU", 165, 190, 5500, 10500),
    ("DEL", "PAT", 100, 120, 3500, 6500),
    ("DEL", "VNS", 80, 95, 3000, 5500),
    
    # Mumbai Hub Routes
    ("BOM", "DEL", 120, 140, 4500, 8500),
    ("BOM", "BLR", 90, 110, 3500, 6500),
    ("BOM", "MAA", 110, 130, 4000, 7500),
    ("BOM", "CCU", 160, 185, 5500, 10000),
    ("BOM", "HYD", 85, 105, 3500, 6500),
    ("BOM", "GOI", 60, 75, 2500, 5000),
    ("BOM", "PNQ", 45, 55, 2000, 4000),
    ("BOM", "AMD", 65, 80, 2500, 5000),
    ("BOM", "COK", 115, 135, 4000, 7500),
    ("BOM", "JAI", 100, 120, 3500, 6500),
    ("BOM", "IDR", 70, 85, 3000, 5500),
    ("BOM", "NAG", 75, 90, 3000, 5500),
    
    # Bengaluru Hub Routes
    ("BLR", "DEL", 150, 175, 5000, 9500),
    ("BLR", "BOM", 90, 110, 3500, 6500),
    ("BLR", "MAA", 55, 70, 2500, 4500),
    ("BLR", "CCU", 155, 175, 5500, 10000),
    ("BLR", "HYD", 65, 80, 2500, 4500),
    ("BLR", "COK", 60, 75, 2500, 4500),
    ("BLR", "GOI", 70, 85, 3000, 5500),
    ("BLR", "PNQ", 90, 105, 3500, 6500),
    ("BLR", "TRV", 70, 85, 3000, 5500),
    
    # Chennai Hub Routes
    ("MAA", "DEL", 160, 185, 5500, 10000),
    ("MAA", "BOM", 110, 130, 4000, 7500),
    ("MAA", "BLR", 55, 70, 2500, 4500),
    ("MAA", "CCU", 145, 165, 5000, 9500),
    ("MAA", "HYD", 70, 85, 3000, 5500),
    ("MAA", "COK", 70, 85, 3000, 5500),
    ("MAA", "TRV", 80, 95, 3500, 6500),
    
    # Kolkata Hub Routes
    ("CCU", "DEL", 130, 155, 4000, 7500),
    ("CCU", "BOM", 160, 185, 5500, 10000),
    ("CCU", "BLR", 155, 175, 5500, 10000),
    ("CCU", "MAA", 145, 165, 5000, 9500),
    ("CCU", "HYD", 130, 150, 4500, 8500),
    ("CCU", "GAU", 70, 85, 3000, 5500),
    ("CCU", "IXB", 55, 70, 2500, 4500),
    ("CCU", "BBI", 65, 80, 2500, 4500),
    ("CCU", "PAT", 60, 75, 2500, 4500),
    ("CCU", "IXR", 55, 70, 2500, 4500),
    
    # Hyderabad Hub Routes
    ("HYD", "DEL", 130, 150, 4500, 8000),
    ("HYD", "BOM", 85, 105, 3500, 6500),
    ("HYD", "BLR", 65, 80, 2500, 4500),
    ("HYD", "MAA", 70, 85, 3000, 5500),
    ("HYD", "CCU", 130, 150, 4500, 8500),
    ("HYD", "VNS", 100, 120, 3500, 6500),
    
    # Tourist/Leisure Routes
    ("GOI", "DEL", 145, 165, 5000, 9000),
    ("GOI", "BOM", 60, 75, 2500, 5000),
    ("GOI", "BLR", 70, 85, 3000, 5500),
    ("SXR", "DEL", 85, 100, 4500, 8500),
    ("SXR", "BOM", 160, 180, 6000, 11000),
    ("ATQ", "DEL", 65, 80, 3000, 5500),
    ("ATQ", "BOM", 135, 155, 5000, 9000),
]

# Typical departure times for different flight types (hour, minute)
DEPARTURE_SLOTS = [
    (5, 30), (6, 0), (6, 30), (6, 45),      # Early morning
    (7, 0), (7, 15), (7, 30), (7, 45),      # Morning rush
    (8, 0), (8, 30), (9, 0), (9, 30),       # Morning
    (10, 0), (10, 30), (11, 0), (11, 30),   # Mid-morning
    (12, 0), (12, 30), (13, 0), (13, 30),   # Afternoon
    (14, 0), (14, 30), (15, 0), (15, 30),   # Afternoon
    (16, 0), (16, 30), (17, 0), (17, 30),   # Evening
    (18, 0), (18, 30), (19, 0), (19, 30),   # Evening rush
    (20, 0), (20, 30), (21, 0), (21, 30),   # Night
    (22, 0), (22, 30), (23, 0),             # Late night
]

# Flight frequency weights (more flights on popular routes)
HIGH_FREQUENCY_ROUTES = [
    ("DEL", "BOM"), ("BOM", "DEL"),
    ("DEL", "BLR"), ("BLR", "DEL"),
    ("BOM", "BLR"), ("BLR", "BOM"),
    ("DEL", "HYD"), ("HYD", "DEL"),
    ("BOM", "HYD"), ("HYD", "BOM"),
]

MEDIUM_FREQUENCY_ROUTES = [
    ("DEL", "MAA"), ("MAA", "DEL"),
    ("DEL", "CCU"), ("CCU", "DEL"),
    ("BOM", "MAA"), ("MAA", "BOM"),
    ("BLR", "MAA"), ("MAA", "BLR"),
    ("DEL", "GOI"), ("GOI", "DEL"),
    ("BOM", "GOI"), ("GOI", "BOM"),
    ("DEL", "AMD"), ("AMD", "DEL"),
]


def create_if_not_exists(session, model, lookup: dict, defaults: dict | None = None):
    """Create record if not exists - used for small reference data."""
    obj = session.query(model).filter_by(**lookup).first()
    if obj:
        return obj
    params = {**lookup}
    if defaults:
        params.update(defaults)
    obj = model(**params)
    session.add(obj)
    session.flush()  # Flush instead of commit for batching
    return obj


def generate_seat_number(row: int, seat_position: int, seats_per_row: int = 6) -> str:
    """Generate realistic seat number like 1A, 12F, 23C etc."""
    seat_letters = {
        6: ['A', 'B', 'C', 'D', 'E', 'F'],
        4: ['A', 'B', 'C', 'D'],
        3: ['A', 'B', 'C'],
    }
    letters = seat_letters.get(seats_per_row, seat_letters[6])
    return f"{row}{letters[seat_position % len(letters)]}"


def generate_seat_templates_data(aircraft_id: int, aircraft) -> list[dict]:
    """Generate seat template data as dictionaries for bulk insert."""
    templates = []
    current_row = 1
    
    # First class (4 seats per row)
    first_count = getattr(aircraft, 'first_count', 0) or 0
    if first_count > 0:
        rows_needed = (first_count + 3) // 4
        created = 0
        for row in range(current_row, current_row + rows_needed):
            for seat_pos in range(4):
                if created < first_count:
                    templates.append({
                        "aircraft_id": aircraft_id,
                        "seat_number": generate_seat_number(row, seat_pos, 4),
                        "seat_class": "First"
                    })
                    created += 1
        current_row += rows_needed + 1
    
    # Business class (6 seats per row)
    business_count = getattr(aircraft, 'business_count', 0) or 0
    if business_count > 0:
        rows_needed = (business_count + 5) // 6
        created = 0
        for row in range(current_row, current_row + rows_needed):
            for seat_pos in range(6):
                if created < business_count:
                    templates.append({
                        "aircraft_id": aircraft_id,
                        "seat_number": generate_seat_number(row, seat_pos, 6),
                        "seat_class": "Business"
                    })
                    created += 1
        current_row += rows_needed
    
    # Premium Economy (6 seats per row)
    premium_count = getattr(aircraft, 'premium_economy_count', 0) or 0
    if premium_count > 0:
        rows_needed = (premium_count + 5) // 6
        created = 0
        for row in range(current_row, current_row + rows_needed):
            for seat_pos in range(6):
                if created < premium_count:
                    templates.append({
                        "aircraft_id": aircraft_id,
                        "seat_number": generate_seat_number(row, seat_pos, 6),
                        "seat_class": "Premium Economy"
                    })
                    created += 1
        current_row += rows_needed
    
    # Economy class (6 seats per row)
    economy_count = getattr(aircraft, 'economy_count', 0) or 0
    if economy_count > 0:
        rows_needed = (economy_count + 5) // 6
        created = 0
        for row in range(current_row, current_row + rows_needed):
            for seat_pos in range(6):
                if created < economy_count:
                    templates.append({
                        "aircraft_id": aircraft_id,
                        "seat_number": generate_seat_number(row, seat_pos, 6),
                        "seat_class": "Economy"
                    })
                    created += 1
    
    return templates


def get_route_frequency(origin: str, dest: str) -> int:
    """Get number of flights per day based on route popularity."""
    route = (origin, dest)
    if route in HIGH_FREQUENCY_ROUTES:
        return random.randint(6, 8)  # Reduced for faster seeding
    elif route in MEDIUM_FREQUENCY_ROUTES:
        return random.randint(3, 5)
    else:
        return random.randint(1, 2)


def get_demand_level(days_ahead: int, is_weekend: bool, is_peak_hour: bool) -> str:
    """Calculate demand level based on various factors."""
    base_score = 0
    if is_weekend:
        base_score += 2
    if is_peak_hour:
        base_score += 2
    if days_ahead <= 3:
        base_score += 3
    elif days_ahead <= 7:
        base_score += 2
    elif days_ahead <= 14:
        base_score += 1
    base_score += random.randint(-1, 2)
    
    if base_score >= 5:
        return "extreme"
    elif base_score >= 3:
        return "high"
    elif base_score >= 1:
        return "medium"
    return "low"


def calculate_dynamic_price(base_min: int, base_max: int, demand_level: str, days_ahead: int) -> float:
    """Calculate price based on demand and booking window."""
    base = random.randint(base_min, base_max)
    demand_multipliers = {"low": 0.85, "medium": 1.0, "high": 1.3, "extreme": 1.6}
    
    if days_ahead <= 3:
        days_multiplier = 1.5
    elif days_ahead <= 7:
        days_multiplier = 1.25
    elif days_ahead <= 14:
        days_multiplier = 1.1
    else:
        days_multiplier = 1.0
    
    price = base * demand_multipliers.get(demand_level, 1.0) * days_multiplier
    return float(round(price / 50) * 50)


def seed():
    """Main seed function with performance optimizations."""
    start_time = time.time()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("⚡ FLIGHTBOOKER DATABASE SEEDING (OPTIMIZED)")
        print("=" * 60)
        
        # =============================================
        # SEED AIRLINES (small dataset - normal insert)
        # =============================================
        print("\n📌 Seeding Airlines...")
        airline_objs = {}
        for name, code in AIRLINES_DATA:
            airline = create_if_not_exists(db, Airline, {"code": code}, {"name": name})
            airline_objs[code] = airline
        db.commit()
        print(f"  ✓ {len(airline_objs)} airlines ready")

        # =============================================
        # SEED AIRPORTS (small dataset - normal insert)
        # =============================================
        print("\n📌 Seeding Airports...")
        airport_objs = {}
        for code, name, city, country in AIRPORTS_DATA:
            airport = create_if_not_exists(
                db, Airport, {"code": code}, 
                {"name": name, "city": city, "country": country}
            )
            airport_objs[code] = airport
        db.commit()
        print(f"  ✓ {len(airport_objs)} airports ready")

        # =============================================
        # SEED AIRCRAFT (small dataset - normal insert)
        # =============================================
        print("\n📌 Seeding Aircraft...")
        aircraft_objs = []
        aircraft_by_id = {}
        for model, capacity, economy, business, premium, first in AIRCRAFT_DATA:
            defaults = {
                "capacity": capacity,
                "economy_count": economy,
                "business_count": business,
                "premium_economy_count": premium,
                "first_count": first,
            }
            aircraft = create_if_not_exists(db, Aircraft, {"model": model}, defaults)
            aircraft_objs.append(aircraft)
            aircraft_by_id[aircraft.id] = aircraft
        db.commit()
        print(f"  ✓ {len(aircraft_objs)} aircraft models ready")

        # =============================================
        # CREATE AIRCRAFT SEAT TEMPLATES (bulk insert)
        # =============================================
        print("\n📌 Creating Aircraft Seat Templates...")
        
        # Check which aircraft already have templates
        existing_template_aircraft = set(
            r[0] for r in db.query(AircraftSeatTemplate.aircraft_id).distinct().all()
        )
        
        all_templates = []
        for aircraft in aircraft_objs:
            if aircraft.id not in existing_template_aircraft:
                templates = generate_seat_templates_data(aircraft.id, aircraft)
                all_templates.extend(templates)
                print(f"  Preparing {len(templates)} templates for {aircraft.model}")
        
        if all_templates:
            # Bulk insert all templates at once
            db.execute(AircraftSeatTemplate.__table__.insert(), all_templates)
            db.commit()
            print(f"  ✓ Bulk inserted {len(all_templates)} seat templates")
        else:
            print(f"  ✓ All templates already exist")

        # =============================================
        # PRE-CACHE SEAT TEMPLATES FOR FAST LOOKUP
        # =============================================
        print("\n📌 Caching seat templates...")
        template_cache = {}
        all_templates_db = db.query(AircraftSeatTemplate).all()
        for tpl in all_templates_db:
            if tpl.aircraft_id not in template_cache:
                template_cache[tpl.aircraft_id] = []
            template_cache[tpl.aircraft_id].append({
                "seat_number": tpl.seat_number,
                "seat_class": tpl.seat_class
            })
        print(f"  ✓ Cached templates for {len(template_cache)} aircraft types")

        # =============================================
        # PRE-FETCH EXISTING FLIGHTS TO AVOID DUPLICATES
        # =============================================
        print("\n📌 Checking existing flights...")
        existing_flights = set()
        for f in db.query(Flight.flight_number, Flight.departure_time).all():
            existing_flights.add((f.flight_number, f.departure_time))
        print(f"  ✓ Found {len(existing_flights)} existing flights")

        # =============================================
        # SEED FLIGHTS FOR NEXT 30 DAYS (BATCHED BULK INSERT)
        # =============================================
        print("\n📌 Seeding Flights for next 30 days...")
        now = datetime.now(timezone.utc)
        
        # Prepare airline and aircraft lists for random selection
        airline_list = list(airline_objs.values())
        
        # Categorize aircraft by capacity for route matching
        short_haul_aircraft = [a for a in aircraft_objs if a.capacity <= 180]
        medium_haul_aircraft = [a for a in aircraft_objs if 150 <= a.capacity <= 220]
        long_haul_aircraft = [a for a in aircraft_objs if a.capacity >= 180]
        
        # Track used flight numbers to avoid duplicates
        used_flight_numbers = set()
        
        # Batch counters
        BATCH_SIZE = 50  # Commit every N flights
        flight_batch = []
        seat_batch = []
        total_flights = 0
        total_seats = 0
        batch_flight_ids = []
        
        for days_ahead in range(0, 31):  # Start from today (day 0)
            day = now + timedelta(days=days_ahead)
            is_weekend = day.weekday() >= 5
            day_flights = 0
            
            for route in ROUTES_DATA:
                origin, dest, dur_min, dur_max, price_min, price_max = route
                
                if origin not in airport_objs or dest not in airport_objs:
                    continue
                
                num_flights = get_route_frequency(origin, dest)
                selected_slots = random.sample(
                    DEPARTURE_SLOTS, 
                    min(num_flights, len(DEPARTURE_SLOTS))
                )
                
                for slot in selected_slots:
                    hour, minute = slot
                    is_peak_hour = hour in [7, 8, 9, 17, 18, 19, 20]
                    
                    dep_time = datetime(day.year, day.month, day.day, hour, minute)
                    duration = random.randint(dur_min, dur_max)
                    arr_time = dep_time + timedelta(minutes=duration)
                    
                    airline = random.choice(airline_list)
                    
                    # Select appropriate aircraft
                    if duration <= 90:
                        aircraft = random.choice(short_haul_aircraft or aircraft_objs)
                    elif duration <= 150:
                        aircraft = random.choice(medium_haul_aircraft or aircraft_objs)
                    else:
                        aircraft = random.choice(long_haul_aircraft or aircraft_objs)
                    
                    # Generate unique flight number
                    flight_number = None
                    for _ in range(20):
                        flight_num = random.randint(100, 9999)
                        candidate = f"{airline.code}{flight_num}"
                        flight_key = (candidate, dep_time.date().isoformat())
                        if flight_key not in used_flight_numbers and (candidate, dep_time) not in existing_flights:
                            flight_number = candidate
                            used_flight_numbers.add(flight_key)
                            break
                    
                    if not flight_number:
                        continue
                    
                    demand_level = get_demand_level(days_ahead, is_weekend, is_peak_hour)
                    base_price = calculate_dynamic_price(price_min, price_max, demand_level, days_ahead)
                    
                    # Create flight object
                    flight = Flight(
                        airline_id=airline.id,
                        aircraft_id=aircraft.id,
                        flight_number=flight_number,
                        departure_airport_id=airport_objs[origin].id,
                        arrival_airport_id=airport_objs[dest].id,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        base_price=base_price,
                        demand_level=demand_level,
                    )
                    
                    db.add(flight)
                    db.flush()  # Get the flight ID without full commit
                    
                    # Create seats from cached templates
                    templates = template_cache.get(aircraft.id, [])
                    if templates:
                        for tpl in templates:
                            is_available = random.random() > 0.1
                            seat_batch.append({
                                "flight_id": flight.id,
                                "seat_number": tpl["seat_number"],
                                "seat_class": tpl["seat_class"],
                                "is_available": is_available
                            })
                    else:
                        # Fallback economy seats
                        cap = getattr(aircraft, 'capacity', 150) or 150
                        seat_count = 0
                        for row in range(1, (cap // 6) + 2):
                            for seat_pos in range(6):
                                if seat_count >= cap:
                                    break
                                is_available = random.random() > 0.1
                                seat_batch.append({
                                    "flight_id": flight.id,
                                    "seat_number": generate_seat_number(row, seat_pos, 6),
                                    "seat_class": "Economy",
                                    "is_available": is_available
                                })
                                seat_count += 1
                    
                    total_flights += 1
                    day_flights += 1
                    
                    # Batch commit for performance
                    if total_flights % BATCH_SIZE == 0:
                        if seat_batch:
                            db.execute(Seat.__table__.insert(), seat_batch)
                            total_seats += len(seat_batch)
                            seat_batch = []
                        db.commit()
                        print(f"    💾 Committed batch: {total_flights} flights, {total_seats} seats", end='\r')
            
            print(f"  Day +{days_ahead:2d} ({day.strftime('%Y-%m-%d')}): {day_flights} flights" + " " * 20)
        
        # Final batch commit
        if seat_batch:
            db.execute(Seat.__table__.insert(), seat_batch)
            total_seats += len(seat_batch)
        db.commit()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETE!")
        print("=" * 60)
        print(f"  ✓ Airlines:  {len(airline_objs)}")
        print(f"  ✓ Airports:  {len(airport_objs)}")
        print(f"  ✓ Aircraft:  {len(aircraft_objs)}")
        print(f"  ✓ Flights:   {total_flights}")
        print(f"  ✓ Seats:     {total_seats}")
        print(f"  ⏱️  Time:     {elapsed:.2f} seconds")
        print("=" * 60)
        
        # Create default admin user
        create_admin_user(db)
        
        # Create airline staff users
        create_airline_staff_users(db, airline_objs)
        
        # Create airport authority users
        create_airport_authority_users(db, airport_objs)
        
        print("\n" + "=" * 60)
        print("📋 STAFF CREDENTIALS SUMMARY")
        print("=" * 60)
        print("ADMIN:")
        print("  Email: admin@flightbooker.com")
        print("  Password: Admin@123")
        print("\nAIRLINE STAFF (example):")
        print("  IndiGo: staff@6e.flightbooker.com / 6EStaff@123")
        print("  Air India: staff@ai.flightbooker.com / AIStaff@123")
        print("\nAIRPORT AUTHORITY (example):")
        print("  Delhi: authority@del.airport.in / DELAuth@123")
        print("  Mumbai: authority@bom.airport.in / BOMAuth@123")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        db.close()


def create_admin_user(db):
    """Create a default admin user if not exists."""
    from app.models.user import User
    from app.auth.password import hash_password
    
    admin_email = os.getenv("ADMIN_EMAIL", "admin@flightbooker.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")
    
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"Admin user already exists: {admin_email}")
        return existing
    
    admin = User(
        email=admin_email,
        password_hash=hash_password(admin_password),
        first_name="FlightBooker",
        last_name="Admin",
        mobile="+919999999999",
        country="India",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Created admin user: {admin_email} with password: {admin_password}")
    return admin


def create_airline_staff_users(db, airlines: dict):
    """Create staff users for each airline."""
    from app.models.user import User
    from app.auth.password import hash_password
    
    print("\n📌 Creating Airline Staff Users...")
    created_count = 0
    
    for airline_code, airline in airlines.items():
        # Create one staff user per airline
        email = f"staff@{airline_code.lower()}.flightbooker.com"
        password = f"{airline_code}Staff@123"
        
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            continue
        
        staff = User(
            email=email,
            password_hash=hash_password(password),
            first_name=f"{airline.name}",
            last_name="Staff",
            mobile=f"+91900000{100 + created_count:04d}",
            country="India",
            role="airline_staff",
            airline_id=airline.id,
            is_active=True,
            is_verified=True,
        )
        db.add(staff)
        created_count += 1
        print(f"  ✓ Created staff for {airline.name}: {email} / {password}")
    
    db.commit()
    print(f"  ✓ {created_count} airline staff users created")
    return created_count


def create_airport_authority_users(db, airports: dict):
    """Create authority users for each airport."""
    from app.models.user import User
    from app.auth.password import hash_password
    
    print("\n📌 Creating Airport Authority Users...")
    created_count = 0
    
    for airport_code, airport in airports.items():
        # Create one authority user per airport
        email = f"authority@{airport_code.lower()}.airport.in"
        password = f"{airport_code}Auth@123"
        
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            continue
        
        authority = User(
            email=email,
            password_hash=hash_password(password),
            first_name=f"{airport.city}",
            last_name="Airport Authority",
            mobile=f"+91800000{100 + created_count:04d}",
            country="India",
            role="airport_authority",
            airport_id=airport.id,
            is_active=True,
            is_verified=True,
        )
        db.add(authority)
        created_count += 1
        print(f"  ✓ Created authority for {airport.code}: {email} / {password}")
    
    db.commit()
    print(f"  ✓ {created_count} airport authority users created")
    return created_count


if __name__ == "__main__":
    seed()
