from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.config import Base


class AircraftSeatTemplate(Base):
    __tablename__ = "aircraft_seat_templates"

    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircrafts.id"), nullable=False)
    seat_number = Column(String(10), nullable=False)
    seat_class = Column(String(30), nullable=False)

    aircraft = relationship("Aircraft")
