from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config import Base


class Aircraft(Base):
    __tablename__ = "aircrafts"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    # total capacity (kept for compatibility)
    capacity = Column(Integer, nullable=False)
    # optional per-class seat counts. If provided these will be used to
    # create seats on a Flight; `capacity` should equal the sum but we'll
    # coerce to the sum when needed.
    economy_count = Column(Integer, default=0)
    premium_economy_count = Column(Integer, default=0)
    business_count = Column(Integer, default=0)
    first_count = Column(Integer, default=0)

    flights = relationship("Flight", back_populates="aircraft")
