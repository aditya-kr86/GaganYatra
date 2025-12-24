# GaganYatra Backend - Setup & Configuration Guide

## Quick Start (Development)

### 1️⃣ Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2️⃣ Initialize Database
```bash
python scripts/seed_db.py
```

### 3️⃣ Start the API Server
```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

✅ **That's it!** The backend is fully functional with:
- Flight search & pricing
- Booking workflow  
- Demand simulation (asyncio background task)
- PNR generation
- PDF receipts

---

## Configuration

### Environment Variables

```bash
# Optional: Database
DATABASE_URL=sqlite:///./database.db  # Default
# DATABASE_URL=postgresql://user:pass@localhost/gagan  # For PostgreSQL

# Optional: Celery (background tasks)
# Use only if you have Redis installed
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Alternative brokers (if Redis not available):
# CELERY_BROKER_URL=memory://  # In-memory (dev only)
# CELERY_BROKER_URL=amqp://guest:guest@localhost//  # RabbitMQ
```

### Database Options

#### SQLite (Default - Development)
```bash
# No setup needed, file-based
# Good for: Testing, development, single-machine setup
DATABASE_URL=sqlite:///./database.db
```

#### PostgreSQL (Recommended - Production)
```bash
# 1. Install PostgreSQL
# 2. Create database
createdb gagan

# 3. Set environment variable
export DATABASE_URL=postgresql://user:password@localhost:5432/gagan

# 4. Start server
uvicorn main:app --reload
```

---

## Background Task Options

### Option 1: Asyncio (Default - No External Dependencies)
✅ **Recommended for development**

- Demand simulator runs as async background task
- No additional services needed
- Automatic restart with server
- Limited to single server instance

**Already enabled by default!** Just start the server:
```bash
uvicorn main:app --reload
```

### Option 2: Celery + Redis (Distributed)
✅ **Recommended for production**

#### Install Redis

**Windows:**
```bash
# Using WSL2 (Windows Subsystem for Linux)
wsl
sudo apt-get install redis-server
sudo service redis-server start
```

Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

#### Start Celery Worker
```bash
# In backend directory
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

For Windows without Redis:
```bash
# Use in-memory broker (development only)
export CELERY_BROKER_URL=memory://
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

---

## Troubleshooting

### Error: "Cannot connect to redis://localhost:6379/0"

**Solution 1: Use default asyncio (recommended)**
- No action needed - the server will work with asyncio background tasks
- You'll see: `⚠️ Celery not available - using asyncio for background tasks`

**Solution 2: Install Redis**
```bash
# Windows with Docker
docker run -d -p 6379:6379 redis:latest

# Then start Celery worker
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

**Solution 3: Use alternative broker**
```bash
# RabbitMQ
export CELERY_BROKER_URL=amqp://guest:guest@localhost//
celery -A app.celery_app.celery_app worker --loglevel=info
```

### Error: "Database locked"

**Cause:** SQLite concurrency issue  
**Solution:** Switch to PostgreSQL for production
```bash
# See PostgreSQL setup above
export DATABASE_URL=postgresql://user:password@localhost/gagan
```

### Port 8000 already in use

```bash
# Use different port
uvicorn main:app --reload --port 8001
```

---

## API Endpoints

### Flight Search
```bash
GET /flights/search?origin=DEL&destination=BOM&date=2025-12-25&tier=ECONOMY&sort_by=price
```

### Create Booking
```bash
POST /bookings/
Content-Type: application/json

{
  "flight_number": "6E123",
  "departure_date": "2025-12-25",
  "passengers": [
    {
      "passenger_name": "John Doe",
      "age": 30,
      "gender": "M"
    }
  ],
  "user_id": 1,
  "seat_class": "ECONOMY"
}
```

### Make Payment
```bash
POST /payments/
Content-Type: application/json

{
  "booking_reference": "BKG12345...",
  "amount": 5000.00,
  "method": "CARD"
}
```

### Get Booking
```bash
GET /bookings/{pnr}
```

### Download Receipt
```bash
GET /bookings/{pnr}/receipt/pdf
```

### User Booking History
```bash
GET /users/{user_id}/bookings?status=Confirmed&limit=50
```

---

## Testing

### Run All Tests
```bash
# Delete old database
rm database.db

# Run tests
python -m pytest backend/tests -v
```

### Run Specific Test File
```bash
python -m pytest backend/tests/test_pricing_engine.py -v
python -m pytest backend/tests/test_booking_workflow.py -v
```

### Test Flight Search
```bash
curl "http://localhost:8000/flights/search?origin=DEL&destination=BOM&date=2025-12-25"
```

---

## Monitoring & Logs

### View API Logs
```bash
# Uvicorn runs with: --log-level info
# For more detail:
uvicorn main:app --reload --log-level debug
```

### Monitor Celery Tasks
```bash
# In separate terminal
celery -A app.celery_app.celery_app events
```

### Check Background Simulator
- View logs in server output
- Search for "[Simulator]" messages
- Interval: Every 5 minutes by default

---

## Production Deployment

### Recommended Setup
```
┌─────────────────────────────────────────┐
│  Nginx (Reverse Proxy)                  │
│  :80 → :8000                           │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Gunicorn (ASGI Server)                 │
│  4 workers × 2 threads                  │
│  :8000                                  │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  FastAPI App                            │
│  + Asyncio background tasks            │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  PostgreSQL (Port 5432)                 │
│  Persistent storage                     │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  Redis (Port 6379) [Optional]           │
│  Celery broker + caching                │
└─────────────────────────────────────────┘
```

### Deploy with Gunicorn
```bash
# Install
pip install gunicorn

# Run (4 workers, async)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 main:app

# With auto-reload on code changes
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 --reload main:app
```

### Environment Variables (Production)
```bash
# .env file or export
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/gagan
CELERY_BROKER_URL=redis://prod_redis:6379/0
DEBUG=false
```

---

## Development Tips

### Auto-format Code
```bash
black backend/app backend/tests
```

### Check Code Quality
```bash
# Lint
pylint backend/app

# Type check
mypy backend/app
```

### Run Specific Endpoint
```bash
# Search flights
python -c "
from app.config import SessionLocal
from app.services.flight_service import search_flights

db = SessionLocal()
flights = search_flights(db, origin='DEL', destination='BOM', limit=5)
for f in flights:
    print(f.flight_number, f.departure_time)
db.close()
"
```

---

## Architecture

```
backend/
├── main.py                 # FastAPI app, routes
├── app/
│   ├── config.py          # DB config, session
│   ├── celery_app.py      # Celery configuration
│   ├── models/            # SQLAlchemy models
│   │   ├── flight.py
│   │   ├── booking.py
│   │   ├── seat.py
│   │   └── ...
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── pricing_engine.py
│   │   ├── flight_service.py
│   │   ├── demand_simulator.py
│   │   └── ...
│   ├── routes/            # API endpoints
│   │   ├── flight_routes.py
│   │   ├── booking_routes.py
│   │   └── ...
│   └── utils/             # Utilities
│       ├── pdf_generator.py
│       ├── pnr_genrator.py
│       └── transaction_retry.py
├── scripts/
│   └── seed_db.py         # Database seeding
├── tests/
│   └── test_*.py          # Test files
├── requirements.txt
└── database.db            # SQLite (development)
```

---

## Support

For issues or questions:
1. Check logs: `uvicorn main:app --reload --log-level debug`
2. Review API docs: http://localhost:8000/docs
3. Check test files for usage examples
4. Verify environment variables are set correctly
