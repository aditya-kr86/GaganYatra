"""
Comprehensive integration tests for booking workflow, payments, and concurrency.
"""
import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
import random


def _ensure_backend_path():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base not in sys.path:
        sys.path.insert(0, base)


_ensure_backend_path()

from app.config import SessionLocal, Base, engine
from app.services.flight_service import create_booking, create_payment, cancel_booking, get_booking_by_pnr
from app.services.pricing_engine import compute_dynamic_price
from app.models.user import User
from app.models.flight import Flight
from app.models.seat import Seat
from app.models.booking import Booking
from scripts.seed_db import seed


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def seeded_db():
    """Seed database with test data."""
    seed()
    db = SessionLocal()
    yield db
    db.close()


def test_booking_workflow_end_to_end(seeded_db):
    """Test complete booking workflow: create → payment → confirmation → PNR."""
    db = seeded_db
    
    # Create test user if not exists
    user = db.query(User).first()
    if not user:
        user = User(full_name="Test User", email="test@example.com", password_hash="test123")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Get a future flight
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    assert flight is not None
    
    # Create booking
    passengers = [
        {"passenger_name": "John Doe", "age": 30, "gender": "M"},
        {"passenger_name": "Jane Doe", "age": 28, "gender": "F"},
    ]
    
    dep_date = flight.departure_time.strftime("%Y-%m-%d")
    result = create_booking(db, user.id, flight.id, dep_date, passengers, seat_class="ECONOMY")
    
    booking = result["booking"]
    total_fare = result["total_fare"]
    
    assert booking is not None
    assert booking.status == "Payment Pending"
    assert len(booking.tickets) == 2
    assert total_fare > 0
    
    # Verify seats were allocated
    for ticket in booking.tickets:
        assert ticket.seat_id is not None
        seat = db.query(Seat).filter(Seat.id == ticket.seat_id).first()
        assert seat is not None
        assert seat.is_available == False
        assert seat.booking_id == booking.id
    
    # Create payment
    payment = create_payment(db, booking.booking_reference, total_fare, "CARD")
    assert payment.status == "SUCCESS"
    assert payment.amount == total_fare
    
    # Verify booking is confirmed and has PNR
    db.refresh(booking)
    assert booking.status == "Confirmed"
    assert booking.pnr is not None
    assert len(booking.pnr) > 0
    
    # Verify tickets have ticket numbers
    for ticket in booking.tickets:
        db.refresh(ticket)
        assert ticket.ticket_number is not None


def test_booking_insufficient_seats(seeded_db):
    """Test booking fails gracefully when not enough seats available."""
    db = seeded_db
    
    user = db.query(User).first()
    if not user:
        user = User(full_name="Test User", email="test@example.com", password_hash="test123")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    
    # Try to book more seats than available
    total_seats = db.query(Seat).filter(Seat.flight_id == flight.id).count()
    
    # Mark most seats as unavailable
    seats = db.query(Seat).filter(Seat.flight_id == flight.id).all()
    for i, seat in enumerate(seats):
        if i < len(seats) - 1:  # Leave only 1 seat available
            seat.is_available = False
    db.commit()
    
    # Try to book 2 passengers (should fail)
    passengers = [
        {"passenger_name": "John Doe", "age": 30, "gender": "M"},
        {"passenger_name": "Jane Doe", "age": 28, "gender": "F"},
    ]
    
    dep_date = flight.departure_time.strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError, match="Not enough seats available"):
        create_booking(db, user.id, flight.id, dep_date, passengers, seat_class="ECONOMY")


def test_booking_cancellation_releases_seats(seeded_db):
    """Test that cancelling a booking releases seats back to inventory."""
    db = seeded_db
    
    user = db.query(User).first()
    if not user:
        user = User(full_name="Test User", email="test@example.com", password_hash="test123")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    
    # Count available seats before booking
    available_before = db.query(Seat).filter(
        Seat.flight_id == flight.id,
        Seat.is_available == True
    ).count()
    
    # Create booking
    passengers = [{"passenger_name": "John Doe", "age": 30, "gender": "M"}]
    dep_date = flight.departure_time.strftime("%Y-%m-%d")
    result = create_booking(db, user.id, flight.id, dep_date, passengers, seat_class="ECONOMY")
    booking = result["booking"]
    
    # Make payment to get PNR
    payment = create_payment(db, booking.booking_reference, result["total_fare"], "CARD")
    db.refresh(booking)
    pnr = booking.pnr
    
    # Count available seats after booking
    available_after_booking = db.query(Seat).filter(
        Seat.flight_id == flight.id,
        Seat.is_available == True
    ).count()
    
    assert available_after_booking == available_before - 1
    
    # Cancel booking
    cancelled = cancel_booking(db, pnr)
    assert cancelled is not None
    assert cancelled.status == "Cancelled"
    
    # Count available seats after cancellation
    available_after_cancel = db.query(Seat).filter(
        Seat.flight_id == flight.id,
        Seat.is_available == True
    ).count()
    
    assert available_after_cancel == available_before


def test_payment_amount_validation(seeded_db):
    """Test payment fails when amount doesn't match booking total."""
    db = seeded_db
    
    user = db.query(User).first()
    if not user:
        user = User(full_name="Test User", email="test@example.com", password_hash="test123")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    
    passengers = [{"passenger_name": "John Doe", "age": 30, "gender": "M"}]
    dep_date = flight.departure_time.strftime("%Y-%m-%d")
    result = create_booking(db, user.id, flight.id, dep_date, passengers, seat_class="ECONOMY")
    
    booking = result["booking"]
    total_fare = result["total_fare"]
    
    # Try to pay with incorrect amount
    with pytest.raises(ValueError, match="amount.*does not match"):
        create_payment(db, booking.booking_reference, total_fare - 100, "CARD")


def test_dynamic_pricing_increases_as_seats_fill(seeded_db):
    """Test that price increases as more seats are booked."""
    db = seeded_db
    
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    
    total_seats = db.query(Seat).filter(Seat.flight_id == flight.id).count()
    
    # Price with many seats available
    price_empty = compute_dynamic_price(
        flight.base_price,
        flight.departure_time,
        total_seats,
        booked_seats=int(total_seats * 0.1),  # 10% full
        demand_level="medium",
        tier="ECONOMY"
    )
    
    # Price with many seats booked
    price_full = compute_dynamic_price(
        flight.base_price,
        flight.departure_time,
        total_seats,
        booked_seats=int(total_seats * 0.9),  # 90% full
        demand_level="medium",
        tier="ECONOMY"
    )
    
    assert price_full > price_empty


def test_pnr_uniqueness(seeded_db):
    """Test that each booking gets a unique PNR."""
    db = seeded_db
    
    user = db.query(User).first()
    if not user:
        user = User(full_name="Test User", email="test@example.com", password_hash="test123")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    flight = db.query(Flight).filter(
        Flight.departure_time > datetime.now(timezone.utc)
    ).first()
    
    pnrs = set()
    
    # Create multiple bookings
    for i in range(3):
        passengers = [{"passenger_name": f"Passenger {i}", "age": 25 + i, "gender": "M"}]
        dep_date = flight.departure_time.strftime("%Y-%m-%d")
        result = create_booking(db, user.id, flight.id, dep_date, passengers, seat_class="ECONOMY")
        booking = result["booking"]
        
        # Make payment to generate PNR
        payment = create_payment(db, booking.booking_reference, result["total_fare"], "CARD")
        db.refresh(booking)
        
        assert booking.pnr is not None
        assert booking.pnr not in pnrs
        pnrs.add(booking.pnr)
    
    assert len(pnrs) == 3
