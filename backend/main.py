from app.config import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth_routes import router as auth_router
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
import sys
import os

# Add scripts folder to path for importing seed module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


app = FastAPI(
    title="FlightBooker - Flight Booking API",
    description="A comprehensive flight booking system with multi-level authentication",
    version="2.0.0",
)

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sim_task = None
_just_seeded = False  # Flag to skip seat reconciliation after fresh seed


def run_seed_if_empty():
    """Run seed script if database is empty."""
    global _just_seeded
    from app.models.airport import Airport
    from app.models.user import User
    from scripts.seed_db import seed
    
    db = SessionLocal()
    try:
        airport_count = db.query(Airport).count()
        admin_count = db.query(User).filter(User.role == "admin").count()
        
        if airport_count == 0 or admin_count == 0:
            print("📦 Database is empty, running seed script...")
            db.close()
            seed()
            _just_seeded = True  # Skip seat reconciliation - seed already created seats
            print("✅ Seed data created successfully!")
        else:
            print(f"📊 Database already has {airport_count} airports and {admin_count} admin(s)")
    except Exception as e:
        print(f"⚠️ Could not check/seed database: {e}")
    finally:
        if db:
            db.close()


@app.on_event("startup")
def create_tables_on_startup():
    global _just_seeded
    # Ensure tables exist on startup for a smooth developer experience
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed database if empty
    run_seed_if_empty()
    
    # Ensure seats exist for existing flights (skip if we just seeded)
    if not _just_seeded:
        try:
            db = SessionLocal()
            created = ensure_all_flight_seats(db)
            if created:
                print(f"✅ Created seats for {created} flights")
        finally:
            db.close()
    else:
        print("⏭️  Skipping seat reconciliation (fresh seed already created seats)")
    
    # Check Celery status
    from app.celery_app import CELERY_ENABLED
    if CELERY_ENABLED:
        print("✅ Celery background task queue enabled (Redis available)")
    else:
        print("⚠️  Celery not available - using asyncio for background tasks")
    
    print("🚀 Application started successfully!")


async def _simulator_loop(interval_minutes: int = 5):
    """Background loop running the demand simulator periodically.

    This function is launched as an asyncio background task on startup.
    It calls `run_demand_simulation_once` and logs results.
    """
    logger = logging.getLogger("gagan.demand_sim")
    
    # Wait a bit before first run to let the app fully start
    await asyncio.sleep(30)  # 30 second delay before first simulation
    
    while True:
        try:
            db = SessionLocal()
            # Limit to fewer flights per run for performance
            updated = run_demand_simulation_once(db, within_hours=168)  # 7 days instead of 30
            if updated:
                logger.info("[Simulator] Updated demand for %s flights", updated)
            db.close()
        except Exception as e:
            logger.exception("[Simulator] Error running simulation: %s", e)
        # sleep
        await asyncio.sleep(interval_minutes * 60)

@app.get("/")
def root():
    return {"message": "welcome to FlightBooker - Flight Booking"}


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

# ============== API Routes ==============

# Authentication (public)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Public routes
app.include_router(flight_router, prefix="/flights", tags=["Flights"])

# User routes (authenticated)
app.include_router(user_router, prefix="/users", tags=["Users"])

# Admin managed resources
app.include_router(airline_router, prefix="/airlines", tags=["Airlines"])
app.include_router(airport_router, prefix="/airports", tags=["Airports"])
app.include_router(aircraft_router, prefix="/aircrafts", tags=["Aircrafts"])
app.include_router(seat_router, prefix="/seats", tags=["Seats"])

# Booking & Payment
app.include_router(booking_router, prefix="/bookings", tags=["Bookings"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(ticket_router, prefix="/tickets", tags=["Tickets"])

# Simulation control (Admin)
from app.routes.demand_routes import router as demand_router
app.include_router(demand_router, prefix="/demand", tags=["Demand Simulator"])


# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



