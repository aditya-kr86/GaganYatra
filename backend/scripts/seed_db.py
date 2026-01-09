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
from itertools import permutations


# ============================================================================
# REALISTIC INDIAN AVIATION DATA
# ============================================================================

AIRLINES_DATA = [
    # (Name, IATA Code)
    ("IndiGo", "6E"),
    ("Air India", "AI")
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
    ("LKO", "Chaudhary Charan Singh International Airport", "Lucknow", "India"),
    ("IXC", "Chandigarh International Airport", "Chandigarh", "India"),
    ("PAT", "Jay Prakash Narayan International Airport", "Patna", "India")
]

AIRCRAFT_DATA = [
    ("Airbus A320neo", 75, 45, 20, 0, 10),
    ("Airbus A321neo", 85, 50, 25, 0, 10),
    ("Boeing 737-800", 75, 45, 20, 0, 10),
    ("Boeing 737 MAX 8", 85, 50, 25, 0, 10)
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


def get_seat_position_type(seat_letter: str, seats_per_row: int = 6) -> str:
    """Determine if seat is window, middle, or aisle based on letter and row configuration."""
    if seats_per_row == 6:
        # 3-3 configuration: A(window), B(middle), C(aisle) | D(aisle), E(middle), F(window)
        if seat_letter in ['A', 'F']:
            return 'window'
        elif seat_letter in ['C', 'D']:
            return 'aisle'
        else:  # B, E
            return 'middle'
    elif seats_per_row == 4:
        # 2-2 configuration: A(window), B(aisle) | C(aisle), D(window)
        if seat_letter in ['A', 'D']:
            return 'window'
        else:  # B, C
            return 'aisle'
    elif seats_per_row == 3:
        # 1-1-1 or similar small config
        if seat_letter == 'A':
            return 'window'
        elif seat_letter == 'C':
            return 'window'
        else:
            return 'aisle'
    return 'middle'  # fallback


def get_seat_surcharge(position_type: str, base_price: float) -> float:
    """Calculate seat surcharge based on position type."""
    surcharge_rates = {
        'window': 0.05,   # 5% extra for window
        'aisle': 0.03,    # 3% extra for aisle
        'middle': 0.0,    # No extra for middle
    }
    rate = surcharge_rates.get(position_type, 0.0)
    return round(base_price * rate, 2)


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
        # SEED FLIGHTS FOR NEXT 30 DAYS (OPTIMIZED FOR CLOUD)
        # =============================================
        print("\n📌 Seeding Flights for next 30 days (all routes, 1-2 flights/route/day)...")
        today = datetime.now(timezone.utc)

        # Use airport codes from previously created airports
        airport_codes = list(airport_objs.keys())

        print(f"✈ Generating all route permutations for {len(airport_codes)} airports...")
        routes = list(permutations(airport_codes, 2))
        print(f"  ✓ Total routes: {len(routes)}")
        print(f"  ✓ Target: {len(routes) * 30 * 1.5:.0f} flights over 30 days")

        # Fetch existing flight keys to avoid duplicates
        existing_flights = set((fn, dt) for fn, dt in db.query(Flight.flight_number, Flight.departure_time).all())

        flight_rows = []
        seat_rows = []
        
        # Batch configuration for efficient cloud insertion
        FLIGHT_BATCH_SIZE = 500
        SEAT_BATCH_SIZE = 5000

        # Generate flights for next 30 days
        flights_generated = 0
        for day_offset in range(0, 30):
            day = today + timedelta(days=day_offset)
            day_flights = 0
            
            for origin, dest in routes:
                # Generate 1-2 flights per route per day
                num_flights = random.randint(1, 2)
                
                for flight_idx in range(num_flights):
                    # Varied departure times throughout the day
                    if flight_idx == 0:
                        dep_hour = random.randint(6, 12)  # Morning flight
                    else:
                        dep_hour = random.randint(15, 21)  # Evening flight
                    
                    dep_min = random.choice([0, 15, 30, 45])
                    dep_time = datetime(day.year, day.month, day.day, dep_hour, dep_min, tzinfo=timezone.utc)

                    # Generate unique flight number
                    airline_code = random.choice(["6E", "AI"])
                    flight_no = f"{airline_code}{random.randint(1000, 9999)}"
                    
                    # Skip if already exists
                    key = (flight_no, dep_time)
                    if key in existing_flights:
                        continue

                    # Calculate flight duration and price
                    duration_min = random.randint(60, 180)
                    base_price = random.randint(2500, 12000)

                    flight_rows.append({
                        "airline_id": airline_objs[airline_code].id,
                        "aircraft_id": random.choice(aircraft_objs).id,
                        "flight_number": flight_no,
                        "departure_airport_id": airport_objs[origin].id,
                        "arrival_airport_id": airport_objs[dest].id,
                        "departure_time": dep_time,
                        "arrival_time": dep_time + timedelta(minutes=duration_min),
                        "base_price": base_price,
                        "demand_level": "medium",
                    })
                    
                    existing_flights.add(key)
                    flights_generated += 1
                    day_flights += 1

                    # Create seats for all 3 classes: First, Business, and Economy
                    # First Class: Row 1 (4 seats per row - A, B, C, D)
                    current_row = 1
                    for s in ['A', 'B', 'C', 'D']:
                        seat_pos = get_seat_position_type(s, 4)
                        seat_rows.append({
                            "flight_number_ref": flight_no,
                            "seat_number": f"{current_row}{s}",
                            "row_number": current_row,
                            "seat_letter": s,
                            "seat_class": "First",
                            "seat_position": seat_pos,
                            "is_available": True,
                            "surcharge": get_seat_surcharge(seat_pos, base_price),
                        })
                    
                    # Business Class: Rows 2-3 (6 seats per row)
                    for r in range(2, 4):
                        for s in ['A', 'B', 'C', 'D', 'E', 'F']:
                            seat_pos = get_seat_position_type(s, 6)
                            seat_rows.append({
                                "flight_number_ref": flight_no,
                                "seat_number": f"{r}{s}",
                                "row_number": r,
                                "seat_letter": s,
                                "seat_class": "Business",
                                "seat_position": seat_pos,
                                "is_available": True,
                                "surcharge": get_seat_surcharge(seat_pos, base_price),
                            })
                    
                    # Economy Class: Rows 4-8 (6 seats per row)
                    for r in range(4, 9):
                        for s in ['A', 'B', 'C', 'D', 'E', 'F']:
                            seat_pos = get_seat_position_type(s, 6)
                            seat_rows.append({
                                "flight_number_ref": flight_no,
                                "seat_number": f"{r}{s}",
                                "row_number": r,
                                "seat_letter": s,
                                "seat_class": "Economy",
                                "seat_position": seat_pos,
                                "is_available": True,
                                "surcharge": get_seat_surcharge(seat_pos, base_price),
                            })
                    
                    # Batch insert flights when batch size is reached
                    if len(flight_rows) >= FLIGHT_BATCH_SIZE:
                        db.execute(Flight.__table__.insert(), flight_rows)
                        db.commit()
                        print(f"  ✓ Inserted batch: {len(flight_rows)} flights")
                        flight_rows = []
            
            print(f"  Day {day_offset + 1}/30: {day_flights} flights scheduled")

        # Insert remaining flights
        if flight_rows:
            print(f"📦 Final flight batch: {len(flight_rows)} flights...")
            db.execute(Flight.__table__.insert(), flight_rows)
            db.commit()

        # Map flight_number -> id for seat assignment
        print(f"📋 Mapping flight IDs...")
        ids = db.execute(
            text("SELECT id, flight_number FROM flights WHERE departure_time >= :start"), 
            {"start": today}
        ).fetchall()
        id_map = {fn: fid for fid, fn in ids}

        # Assign flight_id to seats and batch insert
        print(f"📦 Processing {len(seat_rows)} seats...")
        for seat in seat_rows:
            ref = seat.pop("flight_number_ref", None)
            seat["flight_id"] = id_map.get(ref)
            if seat["flight_id"] is None:
                # Skip seats for flights that weren't created (duplicates)
                continue
        
        # Remove None flight_id seats
        seat_rows = [s for s in seat_rows if s.get("flight_id")]
        
        # Batch insert seats
        seats_inserted = 0
        for i in range(0, len(seat_rows), SEAT_BATCH_SIZE):
            batch = seat_rows[i:i + SEAT_BATCH_SIZE]
            db.execute(Seat.__table__.insert(), batch)
            db.commit()
            seats_inserted += len(batch)
            print(f"  ✓ Inserted seats: {seats_inserted}/{len(seat_rows)}")

        total_flights = flights_generated
        total_seats = len(seat_rows)
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
