from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config import Base


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # Index for fast code lookups
    name = Column(String(200), nullable=False)
    city = Column(String(100), index=True)  # Index for city searches
    country = Column(String(100))

    departures = relationship("Flight", back_populates="departure_airport", foreign_keys='Flight.departure_airport_id')
    arrivals = relationship("Flight", back_populates="arrival_airport", foreign_keys='Flight.arrival_airport_id')

    staff = relationship("User", back_populates="airport")
