from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import get_db
from app.schemas.booking_schema import BookingCreate, BookingResponse, TicketInfoSimplified
from app.services.flight_service import create_booking, get_booking_by_pnr, cancel_booking
from app.models.flight import Flight
from app.schemas.booking_schema import BookingUpdate
from fastapi import Body

router = APIRouter()


def _format_flight_seat(seat_class: str, seat_number: str) -> str:
    """Format flight seat as 'SEAT_CLASS - SEAT_NUMBER' (e.g., 'EC - 32')."""
    # Abbreviate seat class
    seat_class_abbr = {
        "ECONOMY": "EC",
        "ECONOMY_FLEX": "ECF",
        "BUSINESS": "BUS",
        "FIRST": "FC",
    }.get(seat_class.upper(), seat_class[:2].upper())
    
    return f"{seat_class_abbr} - {seat_number}"


def _ticket_to_simplified(ticket) -> TicketInfoSimplified:
    """Convert Ticket model to simplified response format."""
    return TicketInfoSimplified(
        flight_seat=_format_flight_seat(ticket.seat_class or "ECONOMY", ticket.seat_number or ""),
        passenger_name=ticket.passenger_name,
        passenger_age=ticket.passenger_age,
        passenger_gender=ticket.passenger_gender,
        airline_name=ticket.airline_name,
        flight_number=ticket.flight_number,
        route=ticket.route,
        departure_airport=ticket.departure_airport,
        arrival_airport=ticket.arrival_airport,
        departure_city=ticket.departure_city,
        arrival_city=ticket.arrival_city,
        departure_time=ticket.departure_time,
        arrival_time=ticket.arrival_time,
        seat_number=ticket.seat_number or "",
        seat_class=ticket.seat_class or "ECONOMY",
        payment_required=ticket.payment_required,
        currency=ticket.currency,
        ticket_number=ticket.ticket_number,
        issued_at=ticket.issued_at,
    )


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking_api(payload: BookingCreate, db: Session = Depends(get_db)):
    # transform payload passengers to expected dict format
    passengers = []
    for p in payload.passengers:
        pname = p.passenger_name or ""
        entry = {
            "passenger_name": pname,
            "age": p.age,
            "gender": p.gender,
        }
        passengers.append(entry)
    
    # resolve flight_number + departure_date -> flight_id
    from datetime import datetime as dt
    try:
        dep_date_obj = dt.strptime(payload.departure_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid departure_date format. Use YYYY-MM-DD")
    
    # Filter by flight_number AND departure date to get the correct flight
    flight = db.query(Flight).filter(
        Flight.flight_number == payload.flight_number,
        Flight.departure_time >= dt.combine(dep_date_obj, dt.min.time()),
        Flight.departure_time < dt.combine(dep_date_obj, dt.min.time()) + __import__('datetime').timedelta(days=1)
    ).first()
    
    if not flight:
        raise HTTPException(status_code=400, detail=f"flight '{payload.flight_number}' not found on {payload.departure_date}")

    try:
        result = create_booking(
            db,
            user_id=payload.user_id,
            flight_id=flight.id,
            departure_date=payload.departure_date,
            passengers=passengers,
            seat_class=payload.seat_class,
        )
        booking = result["booking"]
        total_fare = result["total_fare"]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    tickets = [_ticket_to_simplified(t) for t in booking.tickets]

    return BookingResponse(
        pnr=booking.pnr,
        booking_reference=booking.booking_reference,
        status=booking.status,
        created_at=booking.created_at,
        total_fare=total_fare,
        tickets=tickets,
        transaction_id=None,
        paid_amount=0.0,
    )


@router.get("/successful", response_model=list[BookingResponse])
def list_successful_bookings_api(db: Session = Depends(get_db)):
    """Retrieve all successful (Confirmed) bookings."""
    from app.models.booking import Booking
    
    bookings = db.query(Booking).filter(Booking.status == "Confirmed").order_by(Booking.created_at.desc()).all()
    
    results = []
    for booking in bookings:
        # Compute total_fare from tickets
        total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
        
        # Convert tickets to simplified format
        tickets = [_ticket_to_simplified(t) for t in booking.tickets]
        
        # Get the most recent successful payment
        successful_payment = None
        if booking.payments:
            successful_payment = next((p for p in sorted(booking.payments, key=lambda x: x.paid_at, reverse=True) if p.status == "Success"), None)
        
        results.append(BookingResponse(
            pnr=booking.pnr,
            booking_reference=booking.booking_reference,
            status=booking.status,
            created_at=booking.created_at,
            total_fare=total_fare,
            tickets=tickets,
            transaction_id=successful_payment.transaction_id if successful_payment else None,
            paid_amount=successful_payment.amount if successful_payment else None,
        ))
    
    return results


@router.get("/{pnr}", response_model=BookingResponse)
def get_booking_api(pnr: str, db: Session = Depends(get_db)):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Compute total_fare from tickets
    total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0

    # Convert tickets to simplified format
    tickets = [_ticket_to_simplified(t) for t in booking.tickets]

    # Get the most recent successful payment
    successful_payment = None
    if booking.payments:
        successful_payment = next((p for p in sorted(booking.payments, key=lambda x: x.paid_at, reverse=True) if p.status == "Success"), None)

    return BookingResponse(
        pnr=booking.pnr,
        booking_reference=booking.booking_reference,
        status=booking.status,
        created_at=booking.created_at,
        total_fare=total_fare,
        tickets=tickets,
        transaction_id=successful_payment.transaction_id if successful_payment else None,
        paid_amount=successful_payment.amount if successful_payment else None,
    )


@router.delete("/{pnr}")
def cancel_booking_api(pnr: str, db: Session = Depends(get_db)):
    booking = cancel_booking(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking cancelled", "pnr": booking.pnr}


@router.patch("/{pnr}", response_model=BookingResponse)
def patch_booking_api(pnr: str, payload: BookingUpdate = Body(...), db: Session = Depends(get_db)):
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    data = payload.dict(exclude_unset=True)
    if "status" in data and data.get("status"):
        booking.status = data.get("status")
    db.commit()
    db.refresh(booking)

    total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
    tickets = [_ticket_to_simplified(t) for t in booking.tickets]

    return BookingResponse(
        pnr=booking.pnr,
        booking_reference=booking.booking_reference,
        status=booking.status,
        created_at=booking.created_at,
        total_fare=total_fare,
        tickets=tickets,
        transaction_id=None,
        paid_amount=None,
    )


@router.get("/{pnr}/receipt/pdf")
def download_booking_receipt_pdf(pnr: str, db: Session = Depends(get_db)):
    """Download booking receipt as PDF."""
    from fastapi.responses import StreamingResponse
    from app.utils.pdf_generator import generate_ticket_pdf
    from app.models.user import User
    
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get user info
    user = db.query(User).filter(User.id == booking.user_id).first()
    user_name = f"{user.first_name} {user.last_name}" if user else "Guest"
    
    # Prepare booking data
    booking_data = {
        'pnr': booking.pnr or booking.booking_reference,
        'booking_reference': booking.booking_reference,
        'status': booking.status,
        'created_at': booking.created_at,
        'user_name': user_name,
    }
    
    # Prepare tickets data
    tickets_data = []
    for ticket in booking.tickets:
        tickets_data.append({
            'ticket_number': ticket.ticket_number or 'PENDING',
            'passenger_name': ticket.passenger_name,
            'flight_number': ticket.flight_number,
            'route': ticket.route,
            'departure_time': ticket.departure_time,
            'arrival_time': ticket.arrival_time,
            'seat_number': ticket.seat_number or 'TBA',
            'seat_class': ticket.seat_class,
            'fare': float(ticket.payment_required or 0.0),
            'currency': ticket.currency or 'INR',
        })
    
    # Generate PDF
    pdf_buffer = generate_ticket_pdf(booking_data, tickets_data)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=booking_{pnr}.pdf"}
    )
