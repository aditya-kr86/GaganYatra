from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from app.config import Base


# Seat position surcharges (percentage of base fare)
SEAT_POSITION_SURCHARGE = {
    "window": 0.05,   # 5% extra for window seats
    "aisle": 0.03,    # 3% extra for aisle seats
    "middle": 0.0,    # No extra charge for middle seats (base price)
}


class Seat(Base):
    __tablename__ = "seats"
    
    # Database indexes for faster seat queries
    __table_args__ = (
        Index('ix_seats_flight_available', 'flight_id', 'is_available'),
        Index('ix_seats_flight_class', 'flight_id', 'seat_class'),
        Index('ix_seats_flight_class_available', 'flight_id', 'seat_class', 'is_available'),
    )

    id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, index=True)

    seat_number = Column(String(5))  # e.g., "12A", "5F"
    row_number = Column(Integer, nullable=True)  # Row number (1, 2, 3...)
    seat_letter = Column(String(1), nullable=True)  # Seat letter (A, B, C...)
    seat_class = Column(Enum("Economy", "Business", "First", name="seat_class"))
    seat_position = Column(Enum("window", "middle", "aisle", name="seat_position"), default="middle")
    is_available = Column(Boolean, default=True)
    surcharge = Column(Float, default=0.0)  # Absolute surcharge amount (computed on creation)

    flight = relationship("Flight", back_populates="seats")
    booking = relationship("Booking", back_populates="seats")
    
    @staticmethod
    def get_position_surcharge_rate(position: str) -> float:
        """Get the surcharge rate (percentage) for a seat position."""
        return SEAT_POSITION_SURCHARGE.get(position, 0.0)
