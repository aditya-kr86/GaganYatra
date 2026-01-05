"""Seed script for FlightBooker backend.

This script is idempotent: running it multiple times won't create duplicate
airlines/airports/aircrafts or flights with the same flight_number + departure_time.

Usage:
    python scripts/seed_db.py

It will create:
- Several airlines
- Several airports
- Several aircraft models (with seat counts)
- Aircraft seat templates for one aircraft
- Multiple flights across the next 30 days between popular city pairs

After running, start the server and call `/flights/search` to see dynamic prices.
"""
from datetime import datetime, timedelta, timezone
import random
import os
import sys

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


def create_if_not_exists(session, model, lookup: dict, defaults: dict | None = None):
    obj = session.query(model).filter_by(**lookup).first()
    if obj:
        return obj
    params = {**lookup}
    if defaults:
        params.update(defaults)
    obj = model(**params)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Airlines
        airlines = [
            ("IndiGo", "6E"),
            ("Air India", "AI"),
            ("SpiceJet", "SG"),
            ("Vistara", "UK"),
        ]
        airline_objs = []
        for name, code in airlines:
            airline_objs.append(create_if_not_exists(db, Airline, {"code": code}, {"name": name}))

        # Airports (code, name, city, country)
        airports = [
            ("DEL", "Indira Gandhi International Airport", "Delhi", "India"),
            ("BOM", "Chhatrapati Shivaji Maharaj Int'l", "Mumbai", "India"),
            ("BLR", "Kempegowda International Airport", "Bengaluru", "India"),
            ("MAA", "Chennai International Airport", "Chennai", "India"),
            ("CCU", "Netaji Subhas Chandra Bose Intl", "Kolkata", "India"),
        ]
        airport_objs = []
        for code, name, city, country in airports:
            airport_objs.append(create_if_not_exists(db, Airport, {"code": code}, {"name": name, "city": city, "country": country}))

        # Aircrafts
        # We'll create three aircraft types with simple capacities and class counts
        ac_data = [
            ("A320neo", 180, {"economy_count": 150, "business_count": 30}),
            ("B737-800", 160, {"economy_count": 140, "business_count": 20}),
            ("A330-300", 280, {"economy_count": 220, "business_count": 40, "premium_economy_count": 20}),
        ]
        aircraft_objs = []
        for model, capacity, extras in ac_data:
            defaults = {"capacity": capacity}
            defaults.update(extras)
            aircraft_objs.append(create_if_not_exists(db, Aircraft, {"model": model}, defaults))

        # Optionally create an aircraft seat template for A330-300 (to demonstrate template path)
        a330 = db.query(Aircraft).filter(Aircraft.model == "A330-300").first()
        if a330:
            # create a small template sample if not exists
            existing = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == a330.id).first()
            if not existing:
                tpl_rows = []
                # First 8 seats as First (1..8), next 40 Business, next 20 Premium, rest Economy
                idx = 1
                for _ in range(8):
                    tpl_rows.append(AircraftSeatTemplate(aircraft_id=a330.id, seat_number=str(idx), seat_class="First"))
                    idx += 1
                for _ in range(40):
                    tpl_rows.append(AircraftSeatTemplate(aircraft_id=a330.id, seat_number=str(idx), seat_class="Business"))
                    idx += 1
                for _ in range(20):
                    tpl_rows.append(AircraftSeatTemplate(aircraft_id=a330.id, seat_number=str(idx), seat_class="Premium Economy"))
                    idx += 1
                for _ in range(212):
                    tpl_rows.append(AircraftSeatTemplate(aircraft_id=a330.id, seat_number=str(idx), seat_class="Economy"))
                    idx += 1
                db.add_all(tpl_rows)
                db.commit()

        # Create flights across next 30 days for selected city pairs
        city_pairs = [
            ("DEL", "BOM"),
            ("DEL", "BLR"),
            ("BOM", "MAA"),
            ("BLR", "CCU"),
            ("MAA", "DEL"),
        ]

        now = datetime.now(timezone.utc)
        flight_count = 0
        for days_ahead in range(1, 31):
            day = now + timedelta(days=days_ahead)
            # create 2-3 flights per pair per day at different times
            for origin, dest in city_pairs:
                num_flights = random.choice([1, 2, 3])
                for i in range(num_flights):
                    dep_time = datetime(day.year, day.month, day.day, 6 + i * 4, random.choice([0, 15, 30, 45]))
                    arr_time = dep_time + timedelta(hours=random.choice([1, 2, 3, 4]))
                    airline = random.choice(airline_objs)
                    aircraft = random.choice(aircraft_objs)
                    flight_number = f"{airline.code}{random.randint(100,999)}"
                    base_price = float(random.randint(3000, 12000))

                    # prevent duplicate flight for same number & departure_time
                    exists = db.query(Flight).filter(Flight.flight_number == flight_number, Flight.departure_time == dep_time).first()
                    if exists:
                        continue

                    f = Flight(
                        airline_id=airline.id,
                        aircraft_id=aircraft.id,
                        flight_number=flight_number,
                        departure_airport_id=db.query(Airport).filter(Airport.code == origin).first().id,
                        arrival_airport_id=db.query(Airport).filter(Airport.code == dest).first().id,
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        base_price=base_price,
                        demand_level=random.choice(["low", "medium", "high"]),
                    )
                    db.add(f)
                    db.commit()
                    db.refresh(f)

                    # create seats for this flight using aircraft template if available
                    templates = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == aircraft.id).all()
                    seats_to_create = []
                    if templates:
                        for tpl in templates:
                            seats_to_create.append(Seat(flight_id=f.id, seat_number=tpl.seat_number, seat_class=tpl.seat_class, is_available=True))
                    else:
                        # use aircraft capacity
                        cap = int(getattr(aircraft, 'capacity', 0) or 150)
                        for sidx in range(1, cap + 1):
                            seats_to_create.append(Seat(flight_id=f.id, seat_number=str(sidx), seat_class="Economy", is_available=True))

                    if seats_to_create:
                        db.add_all(seats_to_create)
                        db.commit()

                    flight_count += 1

        print(f"Seeded {len(airline_objs)} airlines, {len(airport_objs)} airports, {len(aircraft_objs)} aircrafts, {flight_count} flights")
        
        # Create default admin user
        create_admin_user(db)
        
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


if __name__ == "__main__":
    seed()
