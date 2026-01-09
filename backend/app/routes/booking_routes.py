from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.config import get_db
from app.schemas.booking_schema import BookingCreate, BookingResponse, TicketInfoSimplified
from app.services.flight_service import create_booking, get_booking_by_pnr, cancel_booking
from app.services.email_service import send_cancellation_email
from app.models.flight import Flight
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking_schema import BookingUpdate
from app.auth.dependencies import get_current_user, require_admin
from fastapi import Body
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


# ============== Public PNR Status Check ==============

class PNRTicketStatus(BaseModel):
    """Minimal ticket info for public PNR status check."""
    passenger_name: str
    flight_number: str
    route: str  # DEL → BOM
    departure_date: str  # 2026-01-15
    departure_time: str  # 14:30
    seat_number: Optional[str] = None
    seat_class: str

class PNRStatusResponse(BaseModel):
    """Public PNR status response - minimal info without sensitive data."""
    pnr: str
    status: str
    journey_date: str
    tickets: List[PNRTicketStatus]


@router.get("/pnr-status/{pnr}", response_model=PNRStatusResponse)
def check_pnr_status(pnr: str, db: Session = Depends(get_db)):
    """
    Public endpoint to check PNR status without authentication.
    Returns minimal ticket information like real-world airline PNR check.
    """
    # Search by PNR or booking_reference
    booking = db.query(Booking).filter(
        (Booking.pnr == pnr.upper()) | (Booking.booking_reference == pnr)
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=404, 
            detail="PNR not found. Please check the PNR and try again."
        )
    
    if not booking.tickets:
        raise HTTPException(
            status_code=404,
            detail="No tickets found for this PNR."
        )
    
    # Get journey date from first ticket
    first_ticket = booking.tickets[0]
    journey_date = first_ticket.departure_time.strftime("%Y-%m-%d") if first_ticket.departure_time else "N/A"
    
    # Format tickets with minimal info
    tickets = []
    for ticket in booking.tickets:
        tickets.append(PNRTicketStatus(
            passenger_name=ticket.passenger_name,
            flight_number=ticket.flight_number,
            route=f"{ticket.departure_airport} → {ticket.arrival_airport}",
            departure_date=ticket.departure_time.strftime("%Y-%m-%d") if ticket.departure_time else "N/A",
            departure_time=ticket.departure_time.strftime("%H:%M") if ticket.departure_time else "N/A",
            seat_number=ticket.seat_number,
            seat_class=ticket.seat_class,
        ))
    
    return PNRStatusResponse(
        pnr=booking.pnr or booking.booking_reference,
        status=booking.status,
        journey_date=journey_date,
        tickets=tickets,
    )


# ============== Existing Code ==============


def _format_flight_seat(seat_class: str, seat_number: str) -> str:
    """Format flight seat as 'SEAT_CLASS - SEAT_NUMBER' (e.g., 'EC - 32')."""
    # Abbreviate seat class - handle both API tier names and DB names
    seat_class_abbr = {
        # API tier names (uppercase)
        "ECONOMY": "EC",
        "ECONOMY_FLEX": "ECF",
        "BUSINESS": "BUS",
        "FIRST": "FC",
        # Database names (title case)
        "Economy": "EC",
        "Premium Economy": "ECF",
        "Business": "BUS",
        "First": "FC",
    }.get(seat_class, seat_class[:2].upper() if seat_class else "EC")
    
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
def create_booking_api(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new booking. Requires authentication."""
    # transform payload passengers to expected dict format
    passengers = []
    for p in payload.passengers:
        pname = p.passenger_name or ""
        entry = {
            "passenger_name": pname,
            "age": p.age,
            "gender": p.gender,
            "seat_id": p.seat_id,  # Include seat_id if provided per passenger
        }
        passengers.append(entry)
    
    # Use the authenticated user's ID
    user_id = current_user.id
    
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

    # Get selected seat IDs from payload (either from selected_seat_ids list or individual passenger seat_id)
    selected_seat_ids = payload.selected_seat_ids
    if not selected_seat_ids:
        # Try to extract from individual passengers
        seat_ids_from_passengers = [p.get("seat_id") for p in passengers if p.get("seat_id")]
        if len(seat_ids_from_passengers) == len(passengers):
            selected_seat_ids = seat_ids_from_passengers

    try:
        result = create_booking(
            db,
            user_id=user_id,
            flight_id=flight.id,
            departure_date=payload.departure_date,
            passengers=passengers,
            seat_class=payload.seat_class,
            selected_seat_ids=selected_seat_ids,
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


@router.get("/", response_model=list[BookingResponse])
def list_all_bookings_api(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all bookings (admin only)."""
    from app.models.booking import Booking
    
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    
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
def cancel_booking_api(
    pnr: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a booking. Users can only cancel their own bookings. Admins can cancel any."""
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if user owns this booking or is admin
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings")
    
    # Get user email and ticket details before cancellation
    user_email = current_user.email
    total_fare = sum(t.payment_required for t in booking.tickets) if booking.tickets else 0.0
    tickets_data = [
        {
            "passenger_name": t.passenger_name,
            "flight_number": t.flight_number,
            "route": t.route,
            "seat_number": t.seat_number or "N/A",
            "seat_class": t.seat_class or "Economy",
        }
        for t in booking.tickets
    ]
    
    # Cancel the booking
    booking = cancel_booking(db, pnr)
    
    # Send cancellation email in background
    cancellation_data = {
        "pnr": pnr,
        "total_fare": total_fare,
        "refund_amount": total_fare,  # Full refund for now, can add logic for partial
        "tickets": tickets_data,
        "cancelled_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    background_tasks.add_task(send_cancellation_email, user_email, cancellation_data)
    
    return {"message": "Booking cancelled", "pnr": booking.pnr}


@router.patch("/{pnr}", response_model=BookingResponse)
def patch_booking_api(
    pnr: str,
    payload: BookingUpdate = Body(...),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update booking status (Admin only)."""
    booking = get_booking_by_pnr(db, pnr)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    data = payload.model_dump(exclude_unset=True)
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
