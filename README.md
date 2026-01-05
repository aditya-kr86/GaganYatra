# FlightBooker — Flight Booking Simulator with Dynamic Pricing

A high-performance, full-stack airline reservation simulation built using **FastAPI** (backend) and **React 19 + Vite** (frontend).  
The system emulates real-world airline booking logic, including **algorithmic fare fluctuations, transactional seat locking, PNR generation, PDF ticket creation, and email notifications**.

---

## Project Summary

FlightBooker was originally built as part of the **Infosys Springboard Internship Program**.  
The goal of the project is to mirror production-style backend design while simulating airline booking constraints such as:

- **Volatile pricing influenced by inventory, time, and demand**
- **Database-level seat locking to prevent overbooking**
- **Asynchronous demand simulation**
- **Unique PNR creation and QR-enabled PDF receipts**
- **Automated booking emails using SMTP**

---

## Key Achievements

- **Dynamic Pricing Engine:** Fare recalculation on every flight search request.
- **Concurrency Safety:** Uses row-level locks (`SELECT FOR UPDATE` / `with_for_update`) to block parallel seat bookings.
- **End-to-End Booking Simulation:** Seat reservation → PNR → receipt generation → email notification.
- **Automated Assets:** QR-coded PDF ticket and SMTP-based alerts.

---

## Technology Stack

### Backend (Python 3.11+)
- **FastAPI** — asynchronous API framework
- **SQLAlchemy 2.0 ORM** — database modeling & queries
- **PostgreSQL** — row-level locking support
- **Pydantic v2** — data validation & settings
- **Celery + Redis** — async background jobs (email & demand simulation)
- **JWT** — session token generation & role-based access (simulation layer)

### Frontend (React 19)
- **Vite** — fast bundler and dev server
- **React Router 7** — navigation & routing
- **Axios** — API communication with interceptors
- **Lucide-React** — icons
- **Tailwind CSS** — styling framework (custom CSS also supported)

---

## System Design

```
FlightBooker/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT, hashing & RBAC logic
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── routes/        # API endpoints (versioned)
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # Core business logic
│   │   │   ├── pricing_engine.py  # Fare calculation
│   │   │   ├── flight_service.py  # Search & booking logic
│   │   │   └── email_service.py   # SMTP email integration
│   │   └── utils/         # PDF & QR generation helpers
│   └── main.py            # FastAPI entry point
└── frontend/
    ├── src/
    │   ├── api/           # Axios base config & interceptors
    │   ├── components/    # Reusable UI elements
    │   ├── context/       # Auth & booking state providers
    │   └── pages/         # App views
    └── App.jsx            # Root React component
```

---

## Pricing Model (Simulation Formula)

Flight prices are influenced by the following multipliers:

| Multiplier | Description | Behavior |
|---|---|---|
| **Inventory Factor** | Fare increases as seat availability decreases | Inverse scaling |
| **Time Factor** | Fare rises as departure date approaches | Exponential increase |
| **Demand Factor** | Simulated interest impact | Fluctuates dynamically |
| **Cabin Class Factor** | Fixed multiplier for Business/Economy | Static scaling |

*(Actual numeric ranges are defined in the pricing engine module.)*

---

## Core Capabilities

### 1. Intelligent Flight Search
- Multi-airport hub support (Indian airports included)
- Filterable results (price, duration, departure window)
- Pagination-ready API responses for UI efficiency

### 2. Transaction-Safe Booking Flow
- Seat locking via `SELECT FOR UPDATE` to prevent over-allocation
- Bookings wrapped in DB transactions for **atomic seat deduction**
- PNR generated only after successful reservation
- Ticket issued as **QR-embedded PDF**

### 3. Admin & Management Simulation
- Booking, revenue, and flight monitoring dashboard
- Auto-generated PDF tickets
- Email notifications for booking confirmation & cancellation

---

## Installation & Local Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows (Git Bash): venv/Scripts/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/flightbooker
JWT_SECRET_KEY=your_secret_key
SMTP_PASSWORD=your_app_password
SMTP_EMAIL = your_email_address
SMTP_HOST = your_smtp_host  # e.g., smtp.gmail.com
SMTP_PORT = your_smtp_port  # e.g., 587
```

Run the backend server:

```bash
python -m uvicorn main:app --reload --port 8000
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## API Quick Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Returns JWT access token |
| `GET` | `/flights/search` | Flight search with dynamic pricing |
| `POST` | `/bookings/` | Seat lock & booking initiation |
| `GET` | `/bookings/{pnr}/pdf` | Stream generated PDF ticket |

---

## Development Phases

| Phase | Focus | Status |
|---|---|:---:|
| **Phase 1 — Foundation** | DB schema + Flight CRUD APIs | ✅ Completed |
| **Phase 2 — Intelligence** | Dynamic Pricing + Async Demand Simulation | ✅ Completed |
| **Phase 3 — Safety & Security** | Transactions + JWT Session Layer + Seat Locks | ✅ Completed |
| **Phase 4 — Experience** | React UI + PDF & Email Integration + Admin Views | ✅ Completed |

---

## Closing Notes

This project is a **logic-level simulation** and does not process real airline bookings or payments.  
It is intended to study **pricing algorithms, concurrency safety, and backend engineering design for reservation systems**.
