from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Float, Enum
)
from sqlalchemy.orm import relationship
from app.config import Base


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)
    airline_id = Column(Integer, ForeignKey("airlines.id"))
    aircraft_id = Column(Integer, ForeignKey("aircrafts.id"))

    flight_number = Column(String(10), nullable=False)

    departure_airport_id = Column(Integer, ForeignKey("airports.id"))
    arrival_airport_id = Column(Integer, ForeignKey("airports.id"))

    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)

    base_price = Column(Float, nullable=False)

    # Demand level: affects dynamic pricing. Values: low, medium, high, extreme
    demand_level = Column(String(20), nullable=False, default="medium")

    # Flight status: Scheduled, Boarding, Delayed, Departed, Landed, Cancelled
    status = Column(
        Enum("Scheduled", "Boarding", "Delayed", "Departed", "Landed", "Cancelled", name="flight_status"),
        default="Scheduled"
    )
    
    # Gate assignments (managed by airport authority)
    departure_gate = Column(String(10), nullable=True)
    arrival_gate = Column(String(10), nullable=True)
    
    # Delay information (in minutes)
    delay_minutes = Column(Integer, default=0)
    delay_reason = Column(String(200), nullable=True)
    
    # Remarks for FIDS display
    remarks = Column(String(200), nullable=True)

    airline = relationship("Airline", back_populates="flights")
    aircraft = relationship("Aircraft", back_populates="flights")

    departure_airport = relationship("Airport", foreign_keys=[departure_airport_id], back_populates="departures")
    arrival_airport = relationship("Airport", foreign_keys=[arrival_airport_id], back_populates="arrivals")

    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="flight")
