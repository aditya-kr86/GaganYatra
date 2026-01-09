from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, case, literal
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
from app.services.pricing_engine import compute_dynamic_price


_cache: dict = {}
_CACHE_TTL_SECONDS = 60


def _make_cache_key(origin, destination, date, sort_by, days_flex, page, page_size, tier):
    return f"{origin}|{destination}|{date}|{sort_by}|{days_flex}|{page}|{page_size}|{tier}"


def _get_cached(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    ts, value = entry
    import time
    if time.time() - ts > _CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return value


def _set_cached(key: str, value):
    import time
    _cache[key] = (time.time(), value)


def search_flights(db: Session, origin: str | None = None, destination: str | None = None, date: str | None = None, sort_by: str | None = None, limit: int | None = None, days_flex: int = 0, tier: str = "ECONOMY", store_history: bool = False, page: int | None = None, page_size: int | None = None):
    """Search flights with optional filters. Returns list of dicts matching `FlightResponse` schema.
    
    OPTIMIZED: Uses eager loading and batch queries to eliminate N+1 problem.

    origin/destination: airport codes (e.g., 'DEL')
    date: YYYY-MM-DD or None
    sort_by: 'price' or 'duration' or None
    """
    # Check cache first
    cache_key = _make_cache_key(origin, destination, date, sort_by, days_flex or 0, page or 0, page_size or (limit or 0), tier or "ECONOMY")
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # Build optimized query with eager loading of relationships
    query = (
        db.query(Flight)
        .options(
            joinedload(Flight.airline),
            joinedload(Flight.aircraft),
            joinedload(Flight.departure_airport),
            joinedload(Flight.arrival_airport),
        )
    )

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

    # Pagination: support page/page_size OR limit
    if page and page_size:
        offset = max(0, (page - 1) * page_size)
        query = query.offset(offset).limit(page_size)
    elif limit:
        query = query.limit(limit)

    flights = query.all()
    
    if not flights:
        return []

    # OPTIMIZATION: Batch fetch all seat statistics in 2 queries instead of N*7 queries
    flight_ids = [f.id for f in flights]
    
    # Query 1: Get total and available seats per flight in one query
    seat_stats = (
        db.query(
            Seat.flight_id,
            func.count(Seat.id).label('total'),
            func.sum(case((Seat.is_available == True, 1), else_=0)).label('available')
        )
        .filter(Seat.flight_id.in_(flight_ids))
        .group_by(Seat.flight_id)
        .all()
    )
    seat_stats_map = {s.flight_id: {'total': s.total, 'available': s.available or 0} for s in seat_stats}
    
    # Query 2: Get seats by class per flight in one query
    class_stats = (
        db.query(
            Seat.flight_id,
            Seat.seat_class,
            func.sum(case((Seat.is_available == True, 1), else_=0)).label('available')
        )
        .filter(Seat.flight_id.in_(flight_ids))
        .group_by(Seat.flight_id, Seat.seat_class)
        .all()
    )
    
    # Build class stats map: {flight_id: {class_name: count}}
    class_stats_map = {}
    class_mapping = {"Economy": "ECONOMY", "Business": "BUSINESS", "First": "FIRST"}
    for stat in class_stats:
        if stat.flight_id not in class_stats_map:
            class_stats_map[stat.flight_id] = {"ECONOMY": 0, "BUSINESS": 0, "FIRST": 0}
        api_class = class_mapping.get(stat.seat_class, "ECONOMY")
        class_stats_map[stat.flight_id][api_class] = stat.available or 0

    formatted = []
    for flight in flights:
        # Use eager-loaded relationships (no additional queries!)
        airline = flight.airline
        dep = flight.departure_airport
        arr = flight.arrival_airport
        aircraft = flight.aircraft
        
        # Use pre-fetched seat statistics
        stats = seat_stats_map.get(flight.id, {'total': 0, 'available': 0})
        total_seats = stats['total']
        seats_left = stats['available']
        booked_seats = max(total_seats - seats_left, 0)
        
        # Use pre-fetched class statistics
        seats_by_class = class_stats_map.get(flight.id, {"ECONOMY": 0, "BUSINESS": 0, "FIRST": 0})

        # determine demand level (fallback to medium)
        demand_level = getattr(flight, 'demand_level', 'medium') or 'medium'

        # compute dynamic price for requested tier or all tiers
        try:
            if tier and tier.lower() == "all":
                # compute for multiple tiers
                tiers = ["ECONOMY", "BUSINESS", "FIRST"]
                price_map = {}
                for t in tiers:
                    price_map[t] = compute_dynamic_price(
                        base_fare=flight.base_price,
                        departure_time=flight.departure_time,
                        total_seats=total_seats,
                        booked_seats=booked_seats,
                        demand_level=demand_level,
                        tier=t,
                    )
                current_price = price_map.get("ECONOMY", float(flight.base_price or 0.0))
            else:
                current_price = compute_dynamic_price(
                    base_fare=flight.base_price,
                    departure_time=flight.departure_time,
                    total_seats=total_seats,
                    booked_seats=booked_seats,
                    demand_level=demand_level,
                    tier=(tier or "ECONOMY"),
                )
                price_map = None
        except Exception:
            current_price = float(flight.base_price or 0.0)
            price_map = None

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
            "current_price": current_price,
            "price_map": price_map,
            "seats_left": seats_left,
            "seats_by_class": seats_by_class,
        })

    # Cache all search results for short TTL to reduce DB load
    _set_cached(cache_key, formatted)

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


def _get_seat_position_type(seat_letter: str, seats_per_row: int = 6) -> str:
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
        else:
            return 'aisle'
    return 'middle'


def _get_seat_surcharge(position_type: str, base_price: float) -> float:
    """Calculate seat surcharge based on position type."""
    from app.models.seat import SEAT_POSITION_SURCHARGE
    rate = SEAT_POSITION_SURCHARGE.get(position_type, 0.0)
    return round(base_price * rate, 2)


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
        seat_letters_6 = ['A', 'B', 'C', 'D', 'E', 'F']
        
        # If an aircraft seat template exists, use it as the source of truth
        templates = db.query(AircraftSeatTemplate).filter(AircraftSeatTemplate.aircraft_id == aircraft.id).order_by(AircraftSeatTemplate.id.asc()).all()
        if templates:
            for tpl in templates:
                seat_num = tpl.seat_number
                row_num = int(''.join(filter(str.isdigit, seat_num)) or '1')
                seat_letter = ''.join(filter(str.isalpha, seat_num)) or 'A'
                seat_position = _get_seat_position_type(seat_letter, 6)
                surcharge = _get_seat_surcharge(seat_position, base_price)
                
                seats_to_create.append(Seat(
                    flight_id=flight.id,
                    seat_number=seat_num,
                    row_number=row_num,
                    seat_letter=seat_letter,
                    seat_class=tpl.seat_class,
                    seat_position=seat_position,
                    surcharge=surcharge,
                    is_available=True
                ))
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

            # Build seats by class blocks with proper seat numbers
            current_row = 1
            seat_in_row = 0
            
            def add_block(count, cls_name):
                nonlocal current_row, seat_in_row
                for _ in range(count):
                    seat_letter = seat_letters_6[seat_in_row]
                    seat_num = f"{current_row}{seat_letter}"
                    seat_position = _get_seat_position_type(seat_letter, 6)
                    surcharge = _get_seat_surcharge(seat_position, base_price)
                    
                    seats_to_create.append(Seat(
                        flight_id=flight.id,
                        seat_number=seat_num,
                        row_number=current_row,
                        seat_letter=seat_letter,
                        seat_class=cls_name,
                        seat_position=seat_position,
                        surcharge=surcharge,
                        is_available=True
                    ))
                    seat_in_row += 1
                    if seat_in_row >= 6:
                        seat_in_row = 0
                        current_row += 1

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
                for i in range(cap):
                    row = (i // 6) + 1
                    seat_letter = seat_letters_6[i % 6]
                    seat_num = f"{row}{seat_letter}"
                    seat_position = _get_seat_position_type(seat_letter, 6)
                    surcharge = _get_seat_surcharge(seat_position, base_price)
                    
                    seats_to_create.append(Seat(
                        flight_id=flight.id,
                        seat_number=seat_num,
                        row_number=row,
                        seat_letter=seat_letter,
                        seat_class="Economy",
                        seat_position=seat_position,
                        surcharge=surcharge,
                        is_available=True
                    ))

        if seats_to_create:
            db.add_all(seats_to_create)
            db.commit()

    db.refresh(flight)
    return flight


def create_booking(db: Session, user_id: int, flight_id: int, departure_date: str, passengers: list[dict], seat_class: str | None = None, selected_seat_ids: list[int] | None = None) -> dict:
    """Create booking with dynamic price computation and concurrency-safe seat allocation.
    
    Uses row-level locking (SELECT FOR UPDATE) to prevent race conditions when
    multiple users try to book the same seats simultaneously.
    
    If selected_seat_ids is provided, those specific seats will be allocated.
    Otherwise, seats are auto-assigned from available inventory.
    
    Returns dict with 'booking' and 'total_fare' keys.
    """
    from sqlalchemy import text
    
    # Start explicit transaction with row-level lock on flight
    flight = db.query(Flight).filter(Flight.id == flight_id).with_for_update().first()
    if not flight:
        raise ValueError("flight not found")

    # Validate departure_date matches flight
    try:
        from datetime import datetime as dt
        dep_date_obj = dt.strptime(departure_date, "%Y-%m-%d").date()
        flight_date = flight.departure_time.date()
        if dep_date_obj != flight_date:
            raise ValueError(f"departure_date {departure_date} does not match flight departure {flight_date}")
    except ValueError as e:
        raise ValueError(f"Invalid departure_date or mismatch: {e}")

    # Map API tier names to database seat class names
    tier_to_db_class = {
        "ECONOMY": "Economy",
        "ECONOMY_FLEX": "Premium Economy",
        "BUSINESS": "Business",
        "FIRST": "First"
    }
    
    # Get the requested seat class (default to Economy)
    requested_tier = (seat_class or "ECONOMY").upper()
    db_seat_class = tier_to_db_class.get(requested_tier, "Economy")

    # Lock and count available seats with FOR UPDATE to prevent concurrent allocation
    total_seats = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id).scalar() or 0
    
    num_passengers = len(passengers)
    
    # Handle specific seat selection vs auto-assignment
    if selected_seat_ids and len(selected_seat_ids) == num_passengers:
        # User selected specific seats - validate and lock them
        allocated_seats = []
        for seat_id in selected_seat_ids:
            seat = db.query(Seat).filter(
                Seat.id == seat_id,
                Seat.flight_id == flight.id,
                Seat.is_available == True
            ).with_for_update().first()
            
            if not seat:
                raise ValueError(f"Seat ID {seat_id} is not available or does not belong to this flight")
            
            # Validate seat class matches (optional - can be relaxed if needed)
            if seat.seat_class != db_seat_class:
                # Allow seat selection across classes but use the selected seat's class for pricing
                pass  # We'll compute price per seat
            
            allocated_seats.append(seat)
    else:
        # Auto-assign seats from available inventory
        available_seats = db.query(Seat).filter(
            Seat.flight_id == flight.id, 
            Seat.is_available == True,
            Seat.seat_class == db_seat_class
        ).with_for_update().all()
        
        available = len(available_seats)
        if available < num_passengers:
            raise ValueError(f"Not enough {db_seat_class} class seats available. Requested: {num_passengers}, Available: {available}")
        
        allocated_seats = available_seats[:num_passengers]
    
    all_booked = db.query(func.count(Seat.id)).filter(Seat.flight_id == flight.id, Seat.is_available == False).scalar() or 0
    booked_seats = all_booked
    
    demand_level = getattr(flight, 'demand_level', 'medium') or 'medium'
    tier = requested_tier

    dynamic_price = compute_dynamic_price(
        base_fare=flight.base_price,
        departure_time=flight.departure_time,
        total_seats=total_seats,
        booked_seats=booked_seats,
        demand_level=demand_level,
        tier=tier,
    )

    # Calculate total fare including seat surcharges based on seat position
    # Surcharge rates: window = 5%, aisle = 3%, middle = 0%
    from app.models.seat import SEAT_POSITION_SURCHARGE
    
    total_fare = 0.0
    seat_prices = []
    for seat in allocated_seats:
        # Calculate surcharge dynamically based on seat position and current dynamic price
        position = seat.seat_position or "middle"
        surcharge_rate = SEAT_POSITION_SURCHARGE.get(position, 0.0)
        seat_surcharge = round(dynamic_price * surcharge_rate, 2)
        seat_price = dynamic_price + seat_surcharge
        seat_prices.append(seat_price)
        total_fare += seat_price

    # Create booking
    booking_ref = "BKG" + uuid.uuid4().hex[:12].upper()
    booking = Booking(user_id=user_id, pnr=None, booking_reference=booking_ref, status="Payment Pending")
    db.add(booking)
    db.flush()

    airline = db.query(Airline).filter(Airline.id == flight.airline_id).first()
    dep = db.query(Airport).filter(Airport.id == flight.departure_airport_id).first()
    arr = db.query(Airport).filter(Airport.id == flight.arrival_airport_id).first()
    
    # Create tickets for each passenger with computed dynamic price and allocated seat
    for idx, p in enumerate(passengers):
        seat = allocated_seats[idx]
        # Mark seat as unavailable (reserved for this booking)
        seat.is_available = False
        seat.booking_id = booking.id
        
        # Price for this specific seat (includes surcharge)
        passenger_fare = seat_prices[idx]
        
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
            payment_required=passenger_fare,  # Includes seat surcharge
            currency="INR",
            ticket_number=None
        )
        db.add(ticket)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(booking)
    return {"booking": booking, "total_fare": total_fare}


def get_booking_by_pnr(db: Session, pnr: str) -> Booking | None:
    return db.query(Booking).filter(Booking.pnr == pnr.upper()).first()


def cancel_booking(db: Session, pnr: str) -> Booking | None:
    """Cancel booking and release all reserved seats back to inventory."""
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        return None
    
    # Use row-level lock to prevent concurrent modifications
    booking = db.query(Booking).filter(Booking.pnr == pnr.upper()).with_for_update().first()
    if not booking:
        return None
    
    # Release seats back to available inventory
    for ticket in booking.tickets:
        if ticket.seat_id:
            seat = db.query(Seat).filter(Seat.id == ticket.seat_id).with_for_update().first()
            if seat:
                seat.is_available = True
                seat.booking_id = None

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
        required += float(t.payment_required or 0)

    tx = Payment(booking_id=booking.id, amount=amount, method=method, transaction_id=str(uuid.uuid4()))

    # simple validation: require at least the required amount to confirm
    if amount < required:
        tx.status = "Failed"
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    
    # Seats were already reserved during booking creation, no need to check availability again
    # Just verify that the booking has valid seat allocations
    for t in booking.tickets:
        if not t.seat_id:
            # Ticket doesn't have a seat allocated - this shouldn't happen
            tx.status = "Failed"
            db.add(tx)
            db.commit()
            db.refresh(tx)
            return tx

    # amount sufficient and seats already allocated -> success
    tx.status = "Success"
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Confirm booking and issue tickets (seats already allocated during booking)
    booking.status = "Confirmed"
    booking.pnr = _generate_pnr(db)

    for t in booking.tickets:
        # Issue ticket number if not already set
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
    
    OPTIMIZED: Uses bulk queries and batched inserts for performance.
    """
    from sqlalchemy import exists, and_
    
    # Step 1: Find flights WITHOUT any seats (single query)
    flights_with_seats = db.query(Seat.flight_id).distinct().subquery()
    flights_needing_seats = db.query(Flight).filter(
        ~Flight.id.in_(db.query(flights_with_seats.c.flight_id))
    ).all()
    
    if not flights_needing_seats:
        return 0
    
    # Step 2: Pre-cache all aircraft data
    aircraft_cache = {a.id: a for a in db.query(Aircraft).all()}
    
    # Step 3: Pre-cache all seat templates by aircraft_id
    template_cache = {}
    for tpl in db.query(AircraftSeatTemplate).all():
        if tpl.aircraft_id not in template_cache:
            template_cache[tpl.aircraft_id] = []
        template_cache[tpl.aircraft_id].append({
            "seat_number": tpl.seat_number,
            "seat_class": tpl.seat_class
        })
    
    # Step 4: Build all seats in memory
    all_seats = []
    created = 0
    
    for flight in flights_needing_seats:
        aircraft = aircraft_cache.get(flight.aircraft_id)
        if not aircraft or not getattr(aircraft, 'capacity', None):
            continue
        
        templates = template_cache.get(aircraft.id, [])
        
        if templates:
            for tpl in templates:
                all_seats.append({
                    "flight_id": flight.id,
                    "seat_number": tpl["seat_number"],
                    "seat_class": tpl["seat_class"],
                    "is_available": True
                })
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
                    all_seats.append({
                        "flight_id": flight.id,
                        "seat_number": str(idx),
                        "seat_class": cls_name,
                        "is_available": True
                    })
                    idx += 1

            if first > 0:
                add_block(first, "First")
            if bus > 0:
                add_block(bus, "Business")
            if prem > 0:
                add_block(prem, "Premium Economy")
            if eco > 0:
                add_block(eco, "Economy")

            if idx == 1:  # No seats added
                for i in range(1, cap + 1):
                    all_seats.append({
                        "flight_id": flight.id,
                        "seat_number": str(i),
                        "seat_class": "Economy",
                        "is_available": True
                    })
        
        created += 1
    
    # Step 5: Bulk insert all seats at once
    if all_seats:
        # Use batched bulk insert for very large datasets
        BATCH_SIZE = 10000
        for i in range(0, len(all_seats), BATCH_SIZE):
            batch = all_seats[i:i + BATCH_SIZE]
            db.execute(Seat.__table__.insert(), batch)
        db.commit()
    
    return created
