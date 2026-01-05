"""Email service for sending OTPs via Gmail SMTP."""
import smtplib
import random
import string
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import os
from typing import Optional

# In-memory OTP storage (use Redis in production)
_otp_store: dict[str, dict] = {}

# Configuration - Set these in environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mailer91.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # Use 465 for SSL, 587 for STARTTLS
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"  # Use SSL by default
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))

# Set default socket timeoutFailed to send email: (501, b'Bad HELO hostname syntax')
socket.setdefaulttimeout(30)


def get_smtp_ip():
    """Resolve SMTP host to IPv4 address to avoid IPv6 issues."""
    try:
        # Force IPv4 resolution
        result = socket.getaddrinfo(SMTP_HOST, SMTP_PORT, socket.AF_INET, socket.SOCK_STREAM)
        if result:
            return result[0][4][0]  # Return the IP address
    except socket.gaierror:
        pass
    return SMTP_HOST  # Fallback to hostname


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def store_otp(email: str, otp: str) -> None:
    """Store OTP with expiry time."""
    email_lower = email.lower()
    _otp_store[email_lower] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "attempts": 0,
    }
    print(f"[OTP] Stored OTP for {email_lower}: {otp} (expires in {OTP_EXPIRY_MINUTES} min)")
    print(f"[OTP] Current store keys: {list(_otp_store.keys())}")


def verify_otp(email: str, otp: str) -> tuple[bool, str]:
    """
    Verify OTP for an email.
    
    Returns:
        (success, message) tuple
    """
    email = email.lower()
    print(f"[OTP] Verifying OTP for {email}, input: {otp}")
    print(f"[OTP] Current store keys: {list(_otp_store.keys())}")
    stored = _otp_store.get(email)
    
    if not stored:
        print(f"[OTP] No OTP found for {email}")
        return False, "No OTP found. Please request a new one."
    
    # Check expiry
    if datetime.utcnow() > stored["expires_at"]:
        del _otp_store[email]
        return False, "OTP has expired. Please request a new one."
    
    # Check attempts (max 5)
    if stored["attempts"] >= 5:
        del _otp_store[email]
        return False, "Too many failed attempts. Please request a new OTP."
    
    # Verify OTP
    if stored["otp"] != otp:
        stored["attempts"] += 1
        remaining = 5 - stored["attempts"]
        return False, f"Invalid OTP. {remaining} attempts remaining."
    
    # Success - remove OTP from store
    del _otp_store[email]
    return True, "OTP verified successfully."


def clear_otp(email: str) -> None:
    """Clear stored OTP for an email."""
    email = email.lower()
    if email in _otp_store:
        del _otp_store[email]


def send_otp_email(to_email: str, otp: str, purpose: str = "registration") -> tuple[bool, str]:
    """
    Send OTP email using Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        otp: The OTP to send
        purpose: Purpose of OTP (registration, password_reset, etc.)
    
    Returns:
        (success, message) tuple
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        # For development without SMTP configured
        print(f"[DEV MODE] OTP for {to_email}: {otp}")
        return True, "OTP sent (dev mode)"
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your FlightBooker Verification Code: {otp}"
        msg["From"] = f"FlightBooker <{SMTP_EMAIL}>"
        msg["To"] = to_email
        
        # Email body
        text_content = f"""
Hello,

Your verification code for FlightBooker {purpose} is:

{otp}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Safe travels,
The FlightBooker Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; margin: 0; padding: 20px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(249, 115, 22, 0.3); }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .logo span {{ font-size: 24px; font-weight: bold; color: #f97316; }}
        h1 {{ color: white; text-align: center; margin-bottom: 10px; }}
        p {{ color: #9ca3af; line-height: 1.6; }}
        .otp-box {{ background: rgba(249, 115, 22, 0.1); border: 2px solid #f97316; border-radius: 12px; padding: 20px; text-align: center; margin: 30px 0; }}
        .otp-code {{ font-size: 36px; font-weight: bold; color: #f97316; letter-spacing: 8px; }}
        .expiry {{ font-size: 14px; color: #6b7280; margin-top: 10px; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); }}
        .footer p {{ font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <span>✈️ FlightBooker</span>
        </div>
        <h1>Verification Code</h1>
        <p>Hello,</p>
        <p>You've requested a verification code for your FlightBooker account {purpose}. Please use the code below:</p>
        <div class="otp-box">
            <div class="otp-code">{otp}</div>
            <div class="expiry">Expires in {OTP_EXPIRY_MINUTES} minutes</div>
        </div>
        <p>If you didn't request this code, you can safely ignore this email.</p>
        <div class="footer">
            <p>Safe travels,<br>The FlightBooker Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        print(f"[EMAIL] Connecting to SMTP server: {SMTP_HOST}:{SMTP_PORT} (SSL={SMTP_USE_SSL})")
        
        # Send email - use SSL or STARTTLS based on configuration
        if SMTP_USE_SSL:
            # Use SMTP_SSL for port 465 (implicit SSL/TLS)
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")  # Use valid hostname for HELO
        else:
            # Use SMTP with STARTTLS for port 587
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")
            server.starttls()
            server.ehlo("flightbooker.local")
        
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] OTP sent successfully to {to_email}")
        return True, "OTP sent successfully"
    
    except socket.gaierror as e:
        print(f"[EMAIL ERROR] DNS resolution failed: {e}")
        return False, "Network error: Unable to connect to email server. Please check your internet connection."
    except socket.timeout as e:
        print(f"[EMAIL ERROR] Connection timeout: {e}")
        return False, "Connection timeout. Please try again."
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed. Please check SMTP credentials."
    except smtplib.SMTPException as e:
        print(f"[EMAIL ERROR] SMTP error: {e}")
        return False, f"Failed to send email: {str(e)}"
    except Exception as e:
        print(f"[EMAIL ERROR] Unexpected: {e}")
        return False, f"Unexpected error: {str(e)}"


def send_registration_otp(email: str) -> tuple[bool, str]:
    """Generate, store, and send OTP for registration."""
    otp = generate_otp()
    store_otp(email, otp)
    return send_otp_email(email, otp, "registration")


def send_password_reset_otp(email: str) -> tuple[bool, str]:
    """Generate, store, and send OTP for password reset."""
    otp = generate_otp()
    store_otp(email, otp)
    return send_otp_email(email, otp, "password reset")


def send_booking_confirmation_email(
    to_email: str,
    booking_data: dict,
    pdf_bytes: bytes = None
) -> tuple[bool, str]:
    """
    Send booking confirmation email with optional PDF attachment.
    
    Args:
        to_email: Recipient email address
        booking_data: Dict with booking details (pnr, status, tickets, total_fare, etc.)
        pdf_bytes: Optional PDF ticket as bytes
    
    Returns:
        (success, message) tuple
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[DEV MODE] Booking email for {to_email}: PNR={booking_data.get('pnr')}")
        return True, "Email sent (dev mode)"
    
    pnr = booking_data.get('pnr', 'N/A')
    status = booking_data.get('status', 'Unknown')
    total_fare = booking_data.get('total_fare', 0)
    tickets = booking_data.get('tickets', [])
    is_success = status.lower() == 'confirmed'
    
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"{'✅' if is_success else '❌'} FlightBooker Booking {status} - PNR: {pnr}"
        msg["From"] = f"FlightBooker <{SMTP_EMAIL}>"
        msg["To"] = to_email
        
        # Build ticket details HTML
        tickets_html = ""
        for i, ticket in enumerate(tickets):
            tickets_html += f"""
            <div style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                <strong style="color: #f97316;">Passenger {i+1}: {ticket.get('passenger_name', 'N/A')}</strong><br>
                <span style="color: #9ca3af;">
                    {ticket.get('flight_number', '')} | {ticket.get('route', '')} | 
                    Seat: {ticket.get('seat_number', 'TBA')} ({ticket.get('seat_class', 'Economy')})
                </span>
            </div>
            """
        
        # Email HTML
        status_color = "#22c55e" if is_success else "#ef4444"
        status_icon = "✅" if is_success else "❌"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(249, 115, 22, 0.3); }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .logo span {{ font-size: 24px; font-weight: bold; color: #f97316; }}
        .status-badge {{ display: inline-block; background: {status_color}; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; margin: 20px 0; }}
        h1 {{ color: white; text-align: center; margin-bottom: 10px; }}
        h2 {{ color: white; font-size: 18px; margin-top: 25px; margin-bottom: 15px; }}
        p {{ color: #9ca3af; line-height: 1.6; }}
        .pnr-box {{ background: rgba(249, 115, 22, 0.1); border: 2px solid #f97316; border-radius: 12px; padding: 20px; text-align: center; margin: 25px 0; }}
        .pnr-code {{ font-size: 32px; font-weight: bold; color: #f97316; letter-spacing: 4px; }}
        .pnr-label {{ font-size: 12px; color: #6b7280; margin-top: 8px; }}
        .fare-total {{ background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 15px; text-align: center; margin-top: 20px; }}
        .fare-total span {{ color: #22c55e; font-size: 24px; font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); }}
        .footer p {{ font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <span>✈️ FlightBooker</span>
        </div>
        <h1>Booking {status}</h1>
        <p style="text-align: center;">
            <span class="status-badge">{status_icon} {status.upper()}</span>
        </p>
        
        {"" if not is_success else f'''
        <div class="pnr-box">
            <div class="pnr-code">{pnr}</div>
            <div class="pnr-label">Your PNR / Booking Reference</div>
        </div>
        '''}
        
        <h2>Passenger Details</h2>
        {tickets_html if tickets_html else '<p>No passenger details available.</p>'}
        
        {"" if not is_success else f'''
        <div class="fare-total">
            <p style="margin: 0; color: #9ca3af; font-size: 14px;">Total Amount Paid</p>
            <span>₹{total_fare:.2f}</span>
        </div>
        '''}
        
        {"" if not is_success else '<p style="margin-top: 20px;">Your e-ticket is attached to this email. Please carry a copy during your journey.</p>'}
        
        {"<p style='color: #ef4444;'>Unfortunately, your booking could not be completed. Please try again or contact support.</p>" if not is_success else ""}
        
        <div class="footer">
            <p>Thank you for choosing FlightBooker!</p>
            <p>For support, contact us at support@flightbooker.com</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Create alternative container for HTML
        msg_alternative = MIMEMultipart("alternative")
        msg_alternative.attach(MIMEText(f"Booking {status}. PNR: {pnr}", "plain"))
        msg_alternative.attach(MIMEText(html_content, "html"))
        msg.attach(msg_alternative)
        
        # Attach PDF if provided and booking is successful
        if pdf_bytes and is_success:
            pdf_attachment = MIMEBase("application", "pdf")
            pdf_attachment.set_payload(pdf_bytes)
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                "Content-Disposition",
                f"attachment; filename=FlightBooker_Ticket_{pnr}.pdf"
            )
            msg.attach(pdf_attachment)
        
        # Send email
        print(f"[EMAIL] Sending booking confirmation to {to_email} (SSL={SMTP_USE_SSL})")
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")  # Use valid hostname for HELO
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")
            server.starttls()
            server.ehlo("flightbooker.local")
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Booking confirmation sent to {to_email}")
        return True, "Booking confirmation email sent"
    
    except Exception as e:
        print(f"[EMAIL ERROR] Booking email failed: {e}")
        return False, f"Failed to send booking email: {str(e)}"


def send_cancellation_email(
    to_email: str,
    booking_data: dict
) -> tuple[bool, str]:
    """
    Send booking cancellation confirmation email.
    
    Args:
        to_email: Recipient email address
        booking_data: Dict with booking details (pnr, tickets, total_fare, refund_amount, etc.)
    
    Returns:
        (success, message) tuple
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[DEV MODE] Cancellation email for {to_email}: PNR={booking_data.get('pnr')}")
        return True, "Email sent (dev mode)"
    
    pnr = booking_data.get('pnr', 'N/A')
    total_fare = booking_data.get('total_fare', 0)
    refund_amount = booking_data.get('refund_amount', total_fare)
    tickets = booking_data.get('tickets', [])
    cancelled_at = booking_data.get('cancelled_at', datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"❌ FlightBooker Booking Cancelled - PNR: {pnr}"
        msg["From"] = f"FlightBooker <{SMTP_EMAIL}>"
        msg["To"] = to_email
        
        # Build ticket details HTML
        tickets_html = ""
        for i, ticket in enumerate(tickets):
            tickets_html += f"""
            <div style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                <strong style="color: #9ca3af; text-decoration: line-through;">Passenger {i+1}: {ticket.get('passenger_name', 'N/A')}</strong><br>
                <span style="color: #6b7280;">
                    {ticket.get('flight_number', '')} | {ticket.get('route', '')} | 
                    Seat: {ticket.get('seat_number', 'N/A')} ({ticket.get('seat_class', 'Economy')})
                </span>
            </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0a 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(239, 68, 68, 0.3); }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .logo span {{ font-size: 24px; font-weight: bold; color: #f97316; }}
        .status-badge {{ display: inline-block; background: #ef4444; color: white; padding: 8px 20px; border-radius: 20px; font-weight: bold; margin: 20px 0; }}
        h1 {{ color: white; text-align: center; margin-bottom: 10px; }}
        h2 {{ color: white; font-size: 18px; margin-top: 25px; margin-bottom: 15px; }}
        p {{ color: #9ca3af; line-height: 1.6; }}
        .pnr-box {{ background: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; border-radius: 12px; padding: 20px; text-align: center; margin: 25px 0; }}
        .pnr-code {{ font-size: 32px; font-weight: bold; color: #ef4444; letter-spacing: 4px; text-decoration: line-through; }}
        .pnr-label {{ font-size: 12px; color: #6b7280; margin-top: 8px; }}
        .refund-box {{ background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 15px; text-align: center; margin-top: 20px; }}
        .refund-box span {{ color: #22c55e; font-size: 24px; font-weight: bold; }}
        .info-box {{ background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 15px; margin-top: 20px; }}
        .info-box p {{ margin: 5px 0; font-size: 14px; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); }}
        .footer p {{ font-size: 12px; color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <span>✈️ FlightBooker</span>
        </div>
        <h1>Booking Cancelled</h1>
        <p style="text-align: center;">
            <span class="status-badge">❌ CANCELLED</span>
        </p>
        
        <div class="pnr-box">
            <div class="pnr-code">{pnr}</div>
            <div class="pnr-label">Booking Reference (Cancelled)</div>
        </div>
        
        <h2>Cancelled Tickets</h2>
        {tickets_html if tickets_html else '<p>No ticket details available.</p>'}
        
        <div class="refund-box">
            <p style="margin: 0; color: #9ca3af; font-size: 14px;">Refund Amount</p>
            <span>₹{refund_amount:.2f}</span>
            <p style="margin: 5px 0 0; color: #6b7280; font-size: 12px;">Will be credited within 5-7 business days</p>
        </div>
        
        <div class="info-box">
            <p><strong style="color: #3b82f6;">Cancellation Details:</strong></p>
            <p>📅 Cancelled On: {cancelled_at}</p>
            <p>💰 Original Fare: ₹{total_fare:.2f}</p>
            <p>💳 Refund Amount: ₹{refund_amount:.2f}</p>
        </div>
        
        <p style="margin-top: 20px;">Your booking has been successfully cancelled. If you paid online, the refund will be processed to your original payment method.</p>
        
        <div class="footer">
            <p>We hope to see you again soon!</p>
            <p>For support, contact us at support@flightbooker.com</p>
        </div>
    </div>
</body>
</html>
"""
        
        text_content = f"""
Booking Cancelled

Your FlightBooker booking has been cancelled.

PNR: {pnr}
Cancelled On: {cancelled_at}
Original Fare: ₹{total_fare:.2f}
Refund Amount: ₹{refund_amount:.2f}

The refund will be credited to your original payment method within 5-7 business days.

For support, contact us at support@flightbooker.com
"""
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        print(f"[EMAIL] Sending cancellation email to {to_email} (SSL={SMTP_USE_SSL})")
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")  # Use valid hostname for HELO
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            server.ehlo("flightbooker.local")
            server.starttls()
            server.ehlo("flightbooker.local")
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        
        print(f"[EMAIL] Cancellation email sent to {to_email}")
        return True, "Cancellation email sent"
    
    except Exception as e:
        print(f"[EMAIL ERROR] Cancellation email failed: {e}")
        return False, f"Failed to send cancellation email: {str(e)}"
