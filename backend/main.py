from app.config import Base, engine
from fastapi import FastAPI
from app.routes.flight_routes import router as flight_router
from app.routes.booking_routes import router as booking_router
from app.routes.payment_routes import router as payment_router
from app.routes.airport_routes import router as airport_router
from app.routes.airline_routes import router as airline_router
from app.routes.aircraft_routes import router as aircraft_router
from app.routes.user_routes import router as user_router
from app.routes.seat_routes import router as seat_router
from app.routes.ticket_routes import router as ticket_router
from app.config import SessionLocal
from app.services.flight_service import ensure_all_flight_seats


app = FastAPI(title="GaganYatra - Flight Booking")


@app.on_event("startup")
def create_tables_on_startup():
    # Ensure tables exist on startup for a smooth developer experience
    Base.metadata.create_all(bind=engine)
    # Ensure seats exist for existing flights (reconcile seed data)
    try:
        db = SessionLocal()
        created = ensure_all_flight_seats(db)
        if created:
            print(f"✅ Created seats for {created} flights")
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "welcome to GaganYatra - Flight Booking"}

app.include_router(airline_router, prefix="/airlines", tags=["Airlines"])
app.include_router(airport_router, prefix="/airports", tags=["Airports"])
app.include_router(aircraft_router, prefix="/aircrafts", tags=["Aircrafts"])
app.include_router(seat_router, prefix="/seats", tags=["Seats"])

app.include_router(user_router, prefix="/users", tags=["Users"])

app.include_router(flight_router, prefix="/flights", tags=["Flight Search"])

app.include_router(booking_router, prefix="/bookings", tags=["Bookings"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])

app.include_router(ticket_router, prefix="/tickets", tags=["Tickets"])



