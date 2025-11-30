from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from app.config import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_id = Column(Integer, ForeignKey("seats.id"))

    passenger_name = Column(String(100), nullable=False)
    passenger_age = Column(Integer)
    passenger_gender = Column(Enum("M", "F", "Other", name="gender_enum"))

    airline_name = Column(String(100), nullable=False)
    flight_number = Column(String(10), nullable=False)
    route = Column(String(50), nullable=False)

    departure_airport = Column(String(10), nullable=False)
    arrival_airport = Column(String(10), nullable=False)

    departure_city = Column(String(100), nullable=False)
    arrival_city = Column(String(100), nullable=False)

    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)

    seat_number = Column(String(5), nullable=True)
    seat_class = Column(String(20), nullable=False)

    price_paid = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")

    # ticket_number and issued_at are set only after successful payment/issuance
    ticket_number = Column(String(40), unique=True, nullable=True)
    issued_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="tickets")
    flight = relationship("Flight", back_populates="tickets")
    seat = relationship("Seat")
