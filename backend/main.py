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
from app.services.demand_simulator import run_demand_simulation_once
import asyncio
import logging


app = FastAPI(title="GaganYatra - Flight Booking")

_sim_task = None


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
    
    # Check Celery status
    from app.celery_app import CELERY_ENABLED
    if CELERY_ENABLED:
        print("✅ Celery background task queue enabled (Redis available)")
    else:
        print("⚠️  Celery not available - using asyncio for background tasks")


async def _simulator_loop(interval_minutes: int = 5):
    """Background loop running the demand simulator periodically.

    This function is launched as an asyncio background task on startup.
    It calls `run_demand_simulation_once` and logs results.
    """
    logger = logging.getLogger("gagan.demand_sim")
    while True:
        try:
            db = SessionLocal()
            updated = run_demand_simulation_once(db, within_hours=720)
            if updated:
                logger.info("[Simulator] Updated demand for %s flights", updated)
            db.close()
        except Exception as e:
            logger.exception("[Simulator] Error running simulation: %s", e)
        # sleep
        await asyncio.sleep(interval_minutes * 60)

@app.get("/")
def root():
    return {"message": "welcome to GaganYatra - Flight Booking"}


@app.on_event("startup")
async def start_background_tasks():
    # Launch the simulator loop as a background asyncio task
    global _sim_task
    if _sim_task is None:
        _sim_task = asyncio.create_task(_simulator_loop(interval_minutes=5))
        print("🔁 Started demand simulator background task (every 5 minutes)")


@app.on_event("shutdown")
async def stop_background_tasks():
    global _sim_task
    if _sim_task:
        _sim_task.cancel()
        try:
            await _sim_task
        except asyncio.CancelledError:
            pass

app.include_router(airline_router, prefix="/airlines", tags=["Airlines"])
app.include_router(airport_router, prefix="/airports", tags=["Airports"])
app.include_router(aircraft_router, prefix="/aircrafts", tags=["Aircrafts"])
app.include_router(seat_router, prefix="/seats", tags=["Seats"])

app.include_router(user_router, prefix="/users", tags=["Users"])

app.include_router(flight_router, prefix="/flights", tags=["Flight Search"])

# Simulation control
from app.routes.demand_routes import router as demand_router
app.include_router(demand_router, prefix="/demand", tags=["Demand Simulator"])

app.include_router(booking_router, prefix="/bookings", tags=["Bookings"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])

app.include_router(ticket_router, prefix="/tickets", tags=["Tickets"])



