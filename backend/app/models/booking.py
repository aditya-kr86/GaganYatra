from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.config import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # PNR is generated after successful payment; allow null initially
    pnr = Column(String(10), unique=True, nullable=True)
    # Provisional booking reference used to perform payments before ticket issuance
    booking_reference = Column(String(40), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    status = Column(Enum("Payment Pending", "Pending", "Confirmed", "Cancelled", name="booking_status"), default="Payment Pending")

    user = relationship("User", back_populates="bookings")
    tickets = relationship("Ticket", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")
    seats = relationship("Seat", back_populates="booking")
