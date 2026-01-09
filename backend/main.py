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
from app.routes.airline_staff_routes import router as airline_staff_router
from app.routes.airport_authority_routes import router as airport_authority_router
from app.config import SessionLocal
import asyncio
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add scripts folder to path for importing seed module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Thread pool for running blocking DB operations without freezing FastAPI
_executor = ThreadPoolExecutor(max_workers=2)

app = FastAPI(
    title="FlightBooker - Flight Booking API",
    description="A comprehensive flight booking system with multi-level authentication",
    version="2.0.0",
)

# CORS middleware to allow frontend connections
origins = os.getenv("FRONTEND_URLS", "*")
origins_list = [o.strip() for o in origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sim_task = None
_startup_complete = False


def _sync_run_seed_if_empty():
    """Run seed script if database is empty. Runs in thread pool."""
    from app.models.airport import Airport
    from app.models.user import User
    
    db = SessionLocal()
    try:
        airport_count = db.query(Airport).count()
        admin_count = db.query(User).filter(User.role == "admin").count()
        
        if airport_count == 0 or admin_count == 0:
            print("📦 Database is empty, running seed script...")
            db.close()
            from scripts.seed_db import seed
            seed()
            print("✅ Seed data created successfully!")
            return True  # Just seeded
        else:
            print(f"📊 Database already has {airport_count} airports and {admin_count} admin(s)")
            return False
    except Exception as e:
        print(f"⚠️ Could not check/seed database: {e}")
        return False
    finally:
        if db:
            db.close()


@app.on_event("startup")
async def create_tables_on_startup():
    """Non-blocking startup - runs heavy operations in thread pool."""
    global _startup_complete
    
    # Create tables synchronously (fast operation)
    Base.metadata.create_all(bind=engine)
    
    # Run seeding in background thread to not block startup
    loop = asyncio.get_event_loop()
    just_seeded = await loop.run_in_executor(_executor, _sync_run_seed_if_empty)
    
    # Skip seat reconciliation if we just seeded or run it in background
    if not just_seeded:
        # Run seat check in background - don't block startup
        asyncio.create_task(_async_ensure_seats())
    
    _startup_complete = True
    print("🚀 Application started successfully!")


async def _async_ensure_seats():
    """Ensure seats exist - runs in background after startup."""
    await asyncio.sleep(5)  # Wait for app to fully start
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, _sync_ensure_seats)
    except Exception as e:
        logging.warning(f"Seat reconciliation failed: {e}")


def _sync_ensure_seats():
    """Synchronous seat reconciliation - runs in thread pool."""
    from app.services.flight_service import ensure_all_flight_seats
    db = SessionLocal()
    try:
        created = ensure_all_flight_seats(db)
        if created:
            print(f"✅ Created seats for {created} flights")
    finally:
        db.close()


async def _simulator_loop(interval_minutes: int = 10):
    """Background demand simulator - runs in thread pool to avoid blocking."""
    logger = logging.getLogger("gagan.demand_sim")
    
    # Wait longer before first run to let the app fully start
    await asyncio.sleep(60)  # 1 minute delay
    
    while True:
        try:
            loop = asyncio.get_event_loop()
            updated = await loop.run_in_executor(_executor, _sync_run_demand_sim)
            if updated:
                logger.info("[Simulator] Updated demand for %s flights", updated)
        except Exception as e:
            logger.exception("[Simulator] Error running simulation: %s", e)
        
        await asyncio.sleep(interval_minutes * 60)


def _sync_run_demand_sim():
    """Synchronous demand simulation - runs in thread pool."""
    from app.services.demand_simulator import run_demand_simulation_once
    db = SessionLocal()
    try:
        return run_demand_simulation_once(db, within_hours=168)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "welcome to FlightBooker - Flight Booking"}


@app.get("/health")
def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "healthy", "service": "FlightBooker API", "ready": _startup_complete}


@app.on_event("startup")
async def start_background_tasks():
    """Launch background tasks - non-blocking."""
    global _sim_task
    if _sim_task is None:
        _sim_task = asyncio.create_task(_simulator_loop(interval_minutes=10))
        print("🔁 Started demand simulator background task (every 10 minutes)")


@app.on_event("shutdown")
async def stop_background_tasks():
    global _sim_task
    if _sim_task:
        _sim_task.cancel()
        try:
            await _sim_task
        except asyncio.CancelledError:
            pass
    _executor.shutdown(wait=False)

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

# Staff Dashboards
app.include_router(airline_staff_router, prefix="/airline-staff", tags=["Airline Staff"])
app.include_router(airport_authority_router, prefix="/airport-authority", tags=["Airport Authority"])

# Simulation control (Admin)
from app.routes.demand_routes import router as demand_router
app.include_router(demand_router, prefix="/demand", tags=["Demand Simulator"])


# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



