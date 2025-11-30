# **GaganYatra — Flight Booking Simulator with Dynamic Pricing**

A modern Flight Booking & Pricing Simulation system built using **FastAPI**, designed to replicate real-world airline search, pricing algorithms, and booking workflows.

---

## **Project Overview**

GaganYatra simulates core airline operations with:

* **Advanced Flight Search**
* **Dynamic Pricing Engine** (seats, time, demand, fares)
* **Booking Pipeline & PNR Generation**
* **Role-Based Access** (Customer, Airline Staff, Airport Authority)
* **Frontend UI (Jinja2 Templates)**
* **PDF Receipt Generator**

Originally built for the **Infosys Springboard Internship**, the architecture mirrors production-grade backend patterns.

---

## **Tech Stack**

### **Backend**

* FastAPI (Async)
* SQLAlchemy (ORM)
* SQLite / PostgreSQL
* Pydantic v2
* Jinja2 Templates

### **Utilities**

* AsyncIO (background demand simulation)
* ReportLab / WeasyPrint (PDF generation)
* Uvicorn
* Python Dotenv

---

## **Updated ER Diagram (Latest)**
![ER Diagram](ER%20Diagram.png)`

---

## **Project Architecture**

```
GaganYatra/
│
├── backend
│   ├── app/
│   │   ├── models/                 # ORM Models
│   │   ├── routes/                 # FastAPI Routers (module-wise)
│   │   ├── schemas/                # Pydantic Models
│   │   ├── services/               # Business Logic
│   │   │   ├── flight_service.py   # Search + filters
│   │   │   ├── pricing_engine.py   # Dynamic pricing engine
│   │   │   ├── booking_service.py  # Booking + concurrency
│   │   │   └── demand_simulator.py # Background demand updater
│   │   ├── utils/                  # Helpers (PNR, PDF)
│   │   └── config.py               # DB config (SQLite → PostgreSQL)
│   ├── main.py                     # App entry
│   ├── database.db
│   ├── requirements.txt
│   └── README.md
│
├── frontend
│   └── templates/
│
├── ER Diagram.png
├── LICENSE
├── PROJECT_ARCHITECTURE.mmd
└── README.md
```

---

## **Core Features**

### **1. Flight Search & Filters**

* Origin → Destination → Date
* Sorting by fare, departure time, duration
* Real airline/airport dataset simulation

### **2. Dynamic Pricing Engine**

Pricing adjusts based on:

* Remaining seats %
* Time to departure
* Demand index (0–100)
* Fare tiers (economy → first)

Live recalculation during search & booking.

### **3. Booking Workflow**

* Passenger details
* Seat locking (optimistic/pessimistic)
* Payment simulation
* Auto PNR + ticket generation
* Booking history & cancellation support

### **4. Frontend UI**

* Search page
* Real-time pricing results
* Booking page
* Confirmation page
* **PDF / JSON receipt download**

---

## **Setup Instructions**

### **1. Clone Repo**

```bash
git clone https://github.com/aditya-kr86/GaganYatra.git
cd GaganYatra/backend
```

### **2. Virtual Environment**

```bash
python -m venv .venv
source .venv/bin/activate       # mac/Linux
venv\Scripts\activate          # Windows
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Run App**

```bash
uvicorn main:app --reload
```

### **5. Open Browser**

* API: `http://127.0.0.1:8000/docs`
* UI Pages via Jinja2 templates

---

## **Dynamic Pricing Logic (Simplified)**

```
final_price = base_fare
            + (remaining_seats_factor * remaining_seat_ratio)
            + (time_factor * hours_left)
            + (demand_factor * demand_index)
```

Editable inside:
`app/services/pricing_engine.py`

---

## **Project Milestones**

| Module                 | Status         |
| ---------------------- | -------------- |
| Flight Search Engine   | Completed    |
| Dynamic Pricing Engine | In Progress |
| Booking Workflow       | Pending      |
| Frontend Integration   | Pending      |
