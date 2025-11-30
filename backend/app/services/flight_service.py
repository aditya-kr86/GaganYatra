from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
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
from app.models.aircraft_seat_template import AircraftSeatTemplate


def search_flights(db: Session, origin: str | None = None, destination: str | None = None, date: str | None = None, sort_by: str | None = None, limit: int | None = None, days_flex: int = 0):
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
        # Match any departure_time within the calendar date range (00:00:00 <= dt < next day)
        try:
            d_obj = datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            # if parsing fails, leave filter as-is (route already validates format)
            d_obj = None

        if d_obj:
            # expand range by days_flex
            start = d_obj - timedelta(days=abs(int(days_flex)))
            end = d_obj + timedelta(days=abs(int(days_flex)) + 1)
            query = query.filter(Flight.departure_time >= start, Flight.departure_time < end)

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

    # auto-create seats based on the aircraft capacity or per-class counts (if aircraft exists)
    aircraft = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if aircraft and getattr(aircraft, 'capacity', None):
        seats_to_create = []
        # If an aircraft seat template exists, use it as the source of truth
        templates = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == aircraft.id).order_by(AircraftSeatTemplate.id.asc()).all()
        if templates:
            for tpl in templates:
                seats_to_create.append(Seat(flight_id=flight.id, seat_number=tpl.seat_number, seat_class=tpl.seat_class, is_available=True))
        else:
            # prefer per-class counts when provided
            eco = int(getattr(aircraft, 'economy_count', 0) or 0)
            prem = int(getattr(aircraft, 'premium_economy_count', 0) or 0)
            bus = int(getattr(aircraft, 'business_count', 0) or 0)
            first = int(getattr(aircraft, 'first_count', 0) or 0)

            sum_counts = eco + prem + bus + first
            if sum_counts > 0:
                cap = sum_counts
            else:
                cap = int(aircraft.capacity)

            # Build seats by class blocks. Order: First, Business, Premium Economy, Economy
            idx = 1
            def add_block(count, cls_name):
                nonlocal idx
                for _ in range(count):
                    seats_to_create.append(Seat(flight_id=flight.id, seat_number=str(idx), seat_class=cls_name, is_available=True))
                    idx += 1

            if first > 0:
                add_block(first, "First")
            if bus > 0:
                add_block(bus, "Business")
            if prem > 0:
                add_block(prem, "Premium Economy")
            if eco > 0:
                add_block(eco, "Economy")

            # fallback: if no per-class counts and capacity set, create all Economy
            if not seats_to_create:
                for i in range(1, cap + 1):
                    seats_to_create.append(Seat(flight_id=flight.id, seat_number=str(i), seat_class="Economy", is_available=True))

        if seats_to_create:
            db.add_all(seats_to_create)
            db.commit()

    db.refresh(flight)
    return flight


def create_booking(db: Session, user_id: int, flight_id: int, passengers: list[dict], seat_class: str | None = None) -> Booking:
    """Create booking for multiple passengers.

    `passengers` is a list of dicts containing passenger_name, age, gender.
    `seat_ids` (optional) is a list of requested seat ids aligned with passengers.
    `seat_class` (optional) requests seats only within this class when auto-allocating.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise ValueError("flight not found")

    # Seats are not allocated at booking time — allocation happens after successful payment.
    # create booking
    # Create a provisional booking reference to be used for payment.
    booking_ref = "BKG" + uuid.uuid4().hex[:12].upper()
    # PNR will be generated after successful payment
    booking = Booking(user_id=user_id, pnr=None, booking_reference=booking_ref, status="Payment Pending")
    db.add(booking)
    db.flush()

    airline = db.query(Airline).filter(Airline.id == flight.airline_id).first()
    dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()

    # create tickets for each passenger
    for idx, p in enumerate(passengers):
        # tickets created without seat assignment; seats will be allocated after successful payment
        ticket = Ticket(
        booking_id=booking.id,
        flight_id=flight.id,
        seat_id=None,
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
        # DB schema may still enforce NOT NULL for seat_number until migrations run.
        # Use an empty string placeholder for provisional tickets.
        seat_number="",
        seat_class=seat_class if seat_class else "Economy",
        # allow per-passenger fare override if provided in payload
        price_paid=p.get("fare") if p.get("fare") is not None else flight.base_price,
        currency=p.get("currency") if p.get("currency") else "INR",
        # ticket_number will be generated only after payment
        ticket_number=None
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


def create_payment(db: Session, booking_reference: str, amount: float, method: str) -> Payment:
    # lookup booking by booking_reference (booking_id removed from API)
    booking = db.query(Booking).filter(Booking.booking_reference == str(booking_reference)).first()

    if not booking:
        raise ValueError("booking not found")

    # compute required amount from booking tickets
    required = 0.0
    for t in booking.tickets:
        required += float(t.price_paid or 0)

    tx = Payment(booking_id=booking.id, amount=amount, method=method, transaction_id=str(uuid.uuid4()))

    # simple validation: require at least the required amount to confirm
    if amount < required:
        tx.status = "Failed"
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    # before marking success, ensure seats are available for requested classes
    # compute needed per class
    needed_by_class: dict[str, int] = {}
    for t in booking.tickets:
        cls = (t.seat_class or "Economy").strip()
        needed_by_class[cls] = needed_by_class.get(cls, 0) + 1

    for cls, needed in needed_by_class.items():
        cls_norm = cls.strip().lower()
        avail = db.query(func.count(Seat.id)).filter(Seat.flight_id == booking.tickets[0].flight_id, Seat.is_available == True, func.lower(Seat.seat_class) == cls_norm).scalar() or 0
        if avail < needed:
            tx.status = "Failed"
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx

    # amount sufficient and seats available -> success
    tx.status = "Success"
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # allocate seats and issue tickets
    booking.status = "Confirmed"
    booking.pnr = _generate_pnr(db)

    for t in booking.tickets:
        # allocate next available seat for this ticket's class
        cls_norm = (t.seat_class or "Economy").strip().lower()
        seat = db.query(Seat).filter(Seat.flight_id == t.flight_id, Seat.is_available == True, func.lower(Seat.seat_class) == cls_norm).order_by(Seat.id.asc()).with_for_update().first()
        if not seat:
            # this should not happen because we checked availability earlier; treat as failure
            tx.status = "Failed"
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx
        seat.is_available = False
        t.seat_id = seat.id
        t.seat_number = seat.seat_number
        if not t.ticket_number:
            t.ticket_number = "TKT" + uuid.uuid4().hex[:12].upper()
        if not t.issued_at:
            t.issued_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)

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
        # create seats from aircraft counts or templates (use same logic as create_flight)
        aircraft = db.query(Aircraft).filter(Aircraft.id == flight.aircraft_id).first()
        if not aircraft or not getattr(aircraft, 'capacity', None):
            continue

        seats_to_create = []
        templates = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == aircraft.id).order_by(AircraftSeatTemplate.id.asc()).all()
        if templates:
            for tpl in templates:
                seats_to_create.append(Seat(flight_id=flight.id, seat_number=tpl.seat_number, seat_class=tpl.seat_class, is_available=True))
        else:
            eco = int(getattr(aircraft, 'economy_count', 0) or 0)
            prem = int(getattr(aircraft, 'premium_economy_count', 0) or 0)
            bus = int(getattr(aircraft, 'business_count', 0) or 0)
            first = int(getattr(aircraft, 'first_count', 0) or 0)

            sum_counts = eco + prem + bus + first
            cap = sum_counts if sum_counts > 0 else int(aircraft.capacity)

            idx = 1
            def add_block(count, cls_name):
                nonlocal idx
                for _ in range(count):
                    seats_to_create.append(Seat(flight_id=flight.id, seat_number=str(idx), seat_class=cls_name, is_available=True))
                    idx += 1

            if first > 0:
                add_block(first, "First")
            if bus > 0:
                add_block(bus, "Business")
            if prem > 0:
                add_block(prem, "Premium Economy")
            if eco > 0:
                add_block(eco, "Economy")

            if not seats_to_create:
                seats_to_create = [Seat(flight_id=flight.id, seat_number=str(i), seat_class="Economy", is_available=True) for i in range(1, cap+1)]

        if seats_to_create:
            db.add_all(seats_to_create)
            db.commit()
            created += 1

    return created
