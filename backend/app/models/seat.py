from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.config import Base


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)

    seat_number = Column(String(5))
    seat_class = Column(Enum("Economy", "Premium Economy", "Business", "First", name="seat_class"))
    is_available = Column(Boolean, default=True)

    flight = relationship("Flight", back_populates="seats")
    booking = relationship("Booking", back_populates="seats")
