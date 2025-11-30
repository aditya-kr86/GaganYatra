from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import secrets
import uuid

from app.models.flight import Flight
from app.models.airport import Airport
from app.models.airline import Airline
from app.models.seat import Seat
from app.models.booking import Booking
from app.models.ticket import Ticket
from app.models.payment import Payment
from app.models.user import User
from app.models.aircraft import Aircraft


def search_flights(db: Session, origin: str | None = None, destination: str | None = None, date: str | None = None, sort_by: str | None = None, limit: int | None = None):
    """Search flights with optional filters. Returns list of dicts matching `FlightResponse` schema.

    origin/destination: airport codes (e.g., 'DEL')
    date: YYYY-MM-DD or None
    sort_by: 'price' or 'duration' or None
    """
    query = db.query(Flight).join(Airline)

    # filter by related airport codes using relationship `has` to avoid
    # joining the Airport table multiple times (which can cause ambiguous
    # aliases and SQL errors).
    if origin:
        query = query.filter(Flight.departure_airport.has(Airport.code == origin))

    if destination:
        query = query.filter(Flight.arrival_airport.has(Airport.code == destination))

    if date:
        # match date with SQLite's strftime
        query = query.filter(func.strftime('%Y-%m-%d', Flight.departure_time) == date)

    # Apply sorting
    if sort_by == "price":
        query = query.order_by(Flight.base_price.asc())
    elif sort_by == "duration":
        # SQLite doesn't support direct datetime subtraction in SQLAlchemy
        # in a portable way; use julianday difference to compute duration
        query = query.order_by((func.julianday(Flight.arrival_time) - func.julianday(Flight.departure_time)).asc())

    if limit:
        query = query.limit(limit)

    flights = query.all()

    formatted = []
    for flight in flights:
        airline = db.query(Airline).filter(Airline.id == flight.airline_id).first()
        dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
        arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
        aircraft = db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first()

        # compute seats left by counting available seats
        seats_left = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id, Seat.is_available == True).scalar() or 0

        formatted.append({
            "id": flight.id,
            "airline": airline.name if airline else None,
            "flight_number": flight.flight_number,
            "aircraft_model": aircraft.model if aircraft else None,
            "source": dep.code if dep else None,
            "destination": arr.code if arr else None,
            "departure_time": flight.departure_time,
            "arrival_time": flight.arrival_time,
            "base_price": flight.base_price,
            "seats_left": seats_left,
        })

    return formatted


def _generate_pnr(db: Session) -> str:
    """Generate a unique 6-char alphanumeric PNR."""
    for _ in range(10):
        pnr = secrets.token_hex(3).upper()  # 6 hex characters
        exists = db.query(Booking).filter(Booking.pnr == pnr).first()
        if not exists:
            return pnr
    # fallback to UUID-based short PNR
    return uuid.uuid4().hex[:8].upper()


def create_flight(db: Session, airline_id: int, aircraft_id: int, flight_number: str, departure_airport_id: int, arrival_airport_id: int, departure_time: datetime, arrival_time: datetime, base_price: float):
    """Create and persist a new Flight."""
    flight = Flight(
        airline_id=airline_id,
        aircraft_id=aircraft_id,
        flight_number=flight_number,
        departure_airport_id=departure_airport_id,
        arrival_airport_id=arrival_airport_id,
        departure_time=departure_time,
        arrival_time=arrival_time,
        base_price=base_price,
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)

    # auto-create seats based on the aircraft capacity (if aircraft exists)
    aircraft = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if aircraft and getattr(aircraft, 'capacity', None):
        seats_to_create = []
        cap = int(aircraft.capacity)
        # simple seat numbering: 1..capacity
        for i in range(1, cap + 1):
            seats_to_create.append(Seat(flight_id=flight.id, seat_number=str(i), seat_class="Economy", is_available=True))
        if seats_to_create:
            db.add_all(seats_to_create)
            db.commit()

    db.refresh(flight)
    return flight


def create_booking(db: Session, user_id: int, flight_id: int, passengers: list[dict], seat_ids: list[int] | None = None, seat_class: str | None = None) -> Booking:
    """Create booking for multiple passengers.

    `passengers` is a list of dicts containing passenger_name, age, gender.
    `seat_ids` (optional) is a list of requested seat ids aligned with passengers.
    `seat_class` (optional) requests seats only within this class when auto-allocating.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise ValueError("flight not found")

    # Prepare seats: if seat_ids provided validate each; else allocate sequentially
    allocated_seats = []
    if seat_ids:
        if len(seat_ids) != len(passengers):
            raise ValueError("seat_ids length must match passengers length")
        for sid in seat_ids:
            s = db.query(Seat).filter(Seat.id == sid, Seat.flight_id == flight_id, Seat.is_available == True).first()
            if not s:
                raise ValueError(f"requested seat {sid} not available")
            allocated_seats.append(s)
    else:
        # allocate next available seats; if seat_class provided, restrict by class
        if seat_class:
            # match seat_class case-insensitively (e.g. 'economy', 'Economy', 'ECONOMY')
            cls_norm = seat_class.strip().lower()
            available = db.query(Seat).filter(
                Seat.flight_id == flight_id,
                Seat.is_available == True,
                func.lower(Seat.seat_class) == cls_norm
            ).order_by(Seat.id.asc()).limit(len(passengers)).all()
        else:
            available = db.query(Seat).filter(Seat.flight_id == flight_id, Seat.is_available == True).order_by(Seat.id.asc()).limit(len(passengers)).all()

        if len(available) < len(passengers):
            raise ValueError("not enough seats available")
        allocated_seats = available

    # mark seats unavailable
    for s in allocated_seats:
        s.is_available = False

    # create booking
    pnr = _generate_pnr(db)
    booking = Booking(user_id=user_id, pnr=pnr, status="Confirmed")
    db.add(booking)
    db.flush()

    airline = db.query(Airline).filter(Airline.id == flight.airline_id).first()
    dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()

    # create tickets for each passenger
    for idx, p in enumerate(passengers):
        seat = allocated_seats[idx]
        ticket = Ticket(
            booking_id=booking.id,
            flight_id=flight.id,
            seat_id=seat.id,
            passenger_name=p.get("passenger_name"),
            passenger_age=p.get("age"),
            passenger_gender=p.get("gender"),
            airline_name=airline.name if airline else "",
            flight_number=flight.flight_number,
            route=f"{dep.code if dep else ''}-{arr.code if arr else ''}",
            departure_airport=dep.code if dep else "",
            arrival_airport=arr.code if arr else "",
            departure_city=dep.city if dep and hasattr(dep, 'city') else "",
            arrival_city=arr.city if arr and hasattr(arr, 'city') else "",
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            seat_number=seat.seat_number,
            seat_class=seat.seat_class,
            # allow per-passenger fare override if provided in payload
            price_paid=p.get("fare") if p.get("fare") is not None else flight.base_price,
            currency=p.get("currency") if p.get("currency") else "INR",
            ticket_number=("TKT" + uuid.uuid4().hex[:12].upper())
        )
        db.add(ticket)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(booking)
    return booking


def get_booking_by_pnr(db: Session, pnr: str) -> Booking | None:
    return db.query(Booking).filter(Booking.pnr == pnr.upper()).first()


def cancel_booking(db: Session, pnr: str) -> Booking | None:
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        return None
    # free seats
    for ticket in booking.tickets:
        if ticket.seat_id:
            seat = db.query(Seat).filter(Seat.id == ticket.seat_id).first()
            if seat:
                seat.is_available = True

    booking.status = "Cancelled"
    db.commit()
    db.refresh(booking)
    return booking


def create_payment(db: Session, booking_id: int, amount: float, method: str) -> Payment:
    tx = Payment(booking_id=booking_id, amount=amount, method=method, status="Success", transaction_id=str(uuid.uuid4()))
    db.add(tx)
    db.commit()
    db.refresh(tx)
    # link to booking status
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking and tx.status == "Success":
        booking.status = "Confirmed"
        db.commit()
    return tx


def get_payment_by_transaction(db: Session, transaction_id: str) -> Payment | None:
    return db.query(Payment).filter(Payment.transaction_id == transaction_id).first()


def ensure_all_flight_seats(db: Session) -> int:
    """Ensure every flight has Seat rows created based on its aircraft capacity.

    Returns the number of flights for which seats were created.
    """
    created = 0
    flights = db.query(Flight).all()
    for flight in flights:
        # check if flight already has seats
        existing = db.query(Seat).filter(Seat.flight_id == flight.id).first()
        if existing:
            continue
        # create seats from aircraft
        aircraft = db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first()
        if not aircraft or not getattr(aircraft, 'capacity', None):
            continue
        cap = int(aircraft.capacity)
        seats_to_create = [Seat(flight_id=flight.id, seat_number=str(i), seat_class="Economy", is_available=True) for i in range(1, cap+1)]
        if seats_to_create:
            db.add_all(seats_to_create)
            db.commit()
            created += 1

    return created
