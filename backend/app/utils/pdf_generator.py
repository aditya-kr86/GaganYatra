"""
PDF and ticket generation utilities for booking receipts.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas


def generate_ticket_pdf(booking_data: dict, tickets_data: list[dict]) -> BytesIO:
    """
    Generate a PDF ticket/receipt for a booking.
    
    Args:
        booking_data: Dict with keys: pnr, booking_reference, status, created_at, user_name
        tickets_data: List of dicts, each with: ticket_number, passenger_name, flight_number,
                     route, departure_time, arrival_time, seat_number, seat_class, fare
    
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=8
    )
    
    normal_style = styles['Normal']
    
    # Build the PDF content
    elements = []
    
    # Title
    elements.append(Paragraph("✈️ FlightBooker Flight Booking Confirmation", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Booking Information
    elements.append(Paragraph("Booking Details", heading_style))
    
    booking_info = [
        ["PNR:", booking_data.get('pnr', 'N/A')],
        ["Booking Reference:", booking_data.get('booking_reference', 'N/A')],
        ["Status:", booking_data.get('status', 'N/A')],
        ["Booking Date:", booking_data.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M UTC') if isinstance(booking_data.get('created_at'), datetime) else str(booking_data.get('created_at', ''))],
        ["Passenger Name:", booking_data.get('user_name', 'N/A')],
    ]
    
    booking_table = Table(booking_info, colWidths=[2*inch, 4*inch])
    booking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(booking_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Ticket Details
    elements.append(Paragraph("Ticket Information", heading_style))
    
    for idx, ticket in enumerate(tickets_data):
        if idx > 0:
            elements.append(Spacer(1, 0.15*inch))
        
        ticket_info = [
            ["Ticket #:", ticket.get('ticket_number', 'N/A')],
            ["Passenger:", ticket.get('passenger_name', 'N/A')],
            ["Flight:", ticket.get('flight_number', 'N/A')],
            ["Route:", ticket.get('route', 'N/A')],
            ["Departure:", ticket.get('departure_time', '').strftime('%Y-%m-%d %H:%M') if isinstance(ticket.get('departure_time'), datetime) else str(ticket.get('departure_time', ''))],
            ["Arrival:", ticket.get('arrival_time', '').strftime('%Y-%m-%d %H:%M') if isinstance(ticket.get('arrival_time'), datetime) else str(ticket.get('arrival_time', ''))],
            ["Seat:", f"{ticket.get('seat_number', 'N/A')} ({ticket.get('seat_class', 'N/A')})"],
            ["Fare:", f"{ticket.get('currency', 'INR')} {ticket.get('fare', 0.0):.2f}"],
        ]
        
        ticket_table = Table(ticket_info, colWidths=[1.8*inch, 4.2*inch])
        ticket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(ticket_table)
    
    elements.append(Spacer(1, 0.4*inch))
    
    # Total Fare
    total_fare = sum(float(t.get('fare', 0.0)) for t in tickets_data)
    total_text = f"<b>Total Fare: INR {total_fare:.2f}</b>"
    elements.append(Paragraph(total_text, heading_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )
    elements.append(Paragraph("Thank you for choosing FlightBooker!", footer_style))
    elements.append(Paragraph("Please arrive at the airport 2 hours before departure.", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pnr_string(booking_id: int) -> str:
    """
    Generate a unique PNR (Passenger Name Record) string.
    Format: GJYYYYXXXX where YYYY is year and XXXX is booking ID padded.
    
    Args:
        booking_id: Unique booking ID from database
    
    Returns:
        PNR string (e.g., GJ20250123)
    """
    year_suffix = str(datetime.utcnow().year)[-2:]
    pnr = f"GJ{year_suffix}{booking_id:06d}"
    return pnr.upper()


def generate_ticket_pdf_from_booking(booking) -> bytes:
    """
    Generate a PDF ticket from a Booking model object.
    
    Args:
        booking: SQLAlchemy Booking model with tickets relationship
    
    Returns:
        PDF bytes
    """
    # Get user name from first ticket or booking
    user_name = "Guest"
    if booking.tickets:
        user_name = booking.tickets[0].passenger_name
    
    booking_data = {
        "pnr": booking.pnr,
        "booking_reference": booking.booking_reference,
        "status": booking.status,
        "created_at": booking.created_at,
        "user_name": user_name,
    }
    
    tickets_data = []
    for t in booking.tickets:
        tickets_data.append({
            "ticket_number": t.ticket_number,
            "passenger_name": t.passenger_name,
            "flight_number": t.flight_number,
            "route": t.route,
            "departure_time": t.departure_time,
            "arrival_time": t.arrival_time,
            "seat_number": t.seat_number or "TBA",
            "seat_class": t.seat_class or "Economy",
            "fare": t.payment_required or 0.0,
            "currency": t.currency or "INR",
        })
    
    buffer = generate_ticket_pdf(booking_data, tickets_data)
    return buffer.getvalue()
