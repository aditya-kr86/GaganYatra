"""Email service using MSG91 HTTP API for sending OTPs and booking emails."""
import requests
import base64
import random
import string
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

# In-memory OTP storage (use Redis in production)
_otp_store: dict[str, dict] = {}

# Configuration - MSG91 settings
MSG91_AUTHKEY = os.getenv("MSG91_AUTHKEY","449223ArYXhZugN6695ffbc6P1")
SENDER_DOMAIN = os.getenv("SENDER_DOMAIN","mail.ankus.dev")
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
MSG91_API_URL = os.getenv("MSG91_API_URL", "https://control.msg91.com/api/v5/email/send")


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def store_otp(email: str, otp: str) -> None:
    """Store OTP with expiry time."""
    email_lower = email.lower()
    _otp_store[email_lower] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
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
    if datetime.now(timezone.utc) > stored["expires_at"]:
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


def _send_msg91(payload: dict) -> tuple[bool, str]:
    """Send payload to MSG91 API and return (success, message)."""
    if not MSG91_AUTHKEY or not SENDER_DOMAIN:
        print(f"[DEV MODE] MSG91 payload (not sent): {payload}")
        return True, "Email sent (dev mode)"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authkey": MSG91_AUTHKEY,
    }

    try:
        resp = requests.post(MSG91_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code // 100 == 2:
            return True, "Email sent successfully"
        else:
            return False, f"MSG91 error {resp.status_code}: {resp.text}"
    except requests.RequestException as e:
        return False, f"Network error: {str(e)}"


def send_registration_otp(email: str, name: str | None = None) -> tuple[bool, str]:
    """Generate, store, and send OTP for registration via MSG91 template."""
    otp = generate_otp()
    store_otp(email, otp)

    payload = {
            "template_id": "flightbooker_otp",
            "from": {"name": "FlightBooker", "email": f"no-reply@{SENDER_DOMAIN}"},
            "domain": SENDER_DOMAIN,
            "reply_to": [
                {"email": f"support@{SENDER_DOMAIN}"},
                {"email": f"admin@{SENDER_DOMAIN}"}
            ],
            "attachments": [],
            "recipients": [
                {
                    "to": [
                        {"name": name or "", "email": email}
                    ],
                    "variables": {
                        "purpose": "registration",
                        "otp": otp,
                        "expiry_minutes": str(OTP_EXPIRY_MINUTES),
                    }
                }
            ]
    }

    return _send_msg91(payload)


def send_password_reset_otp(email: str, name: str | None = None) -> tuple[bool, str]:
    """Generate, store, and send OTP for password reset via MSG91 template."""
    otp = generate_otp()
    store_otp(email, otp)

    payload = {
            "template_id": "flightbooker_otp",
            "from": {"name": "FlightBooker", "email": f"no-reply@{SENDER_DOMAIN}"},
            "domain": SENDER_DOMAIN,
            "reply_to": [
                {"email": f"support@{SENDER_DOMAIN}"},
                {"email": f"admin@{SENDER_DOMAIN}"}
            ],
            "attachments": [],
            "recipients": [
                {
                    "to": [
                        {"name": name or "", "email": email}
                    ],
                    "variables": {
                        "purpose": "password reset",
                        "otp": otp,
                        "expiry_minutes": str(OTP_EXPIRY_MINUTES),
                    }
                }
            ]
    }

    return _send_msg91(payload)


def send_booking_confirmation_email(
    to_email: str,
    booking_data: dict,
    pdf_bytes: bytes = None,
    recipient_name: str | None = None,
) -> tuple[bool, str]:
    """Send booking confirmation using MSG91 template with optional PDF attachment."""
    pnr = booking_data.get("pnr", "N/A")
    status = booking_data.get("status", "Unknown")
    total_fare = booking_data.get("total_fare", 0)
    tickets = booking_data.get("tickets", [])
    is_success = str(status).lower() == "confirmed"

    # Build tickets_html for template variable
    tickets_html = ""
    for i, ticket in enumerate(tickets):
        tickets_html += (
            f"<div><strong>Passenger {i+1}: {ticket.get('passenger_name','N/A')}</strong><br>"
            f"{ticket.get('flight_number','')} | {ticket.get('route','')} | Seat: {ticket.get('seat_number','TBA')} ({ticket.get('seat_class','Economy')})</div>"
        )

    payload = {
        "recipients": [
            {
                "to": [{"email": to_email, "name": recipient_name or ""}],
                "variables": {
                    "status": status,
                    "pnr": pnr,
                    "total_fare": f"{total_fare:.2f}",
                    "tickets_html": tickets_html,
                },
            }
        ],
        "from": {"name": "FlightBooker", "email": f"no-reply@{SENDER_DOMAIN}"},
        "domain": SENDER_DOMAIN,
        "template_id": "flightbooker_confirm" if is_success else "flightbooker_cancel",
    }

    # Attach PDF if provided and booking confirmed
    if pdf_bytes and is_success:
        pdf_base64 = base64.b64encode(pdf_bytes).decode()
        pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"
        payload["attachments"] = [{"file": pdf_data_uri, "fileName": f"FlightBooker_Ticket_{pnr}.pdf"}]

    return _send_msg91(payload)


def send_cancellation_email(to_email: str, booking_data: dict, recipient_name: str | None = None) -> tuple[bool, str]:
    """Send booking cancellation using MSG91 template."""
    pnr = booking_data.get("pnr", "N/A")
    total_fare = booking_data.get("total_fare", 0)
    refund_amount = booking_data.get("refund_amount", total_fare)
    tickets = booking_data.get("tickets", [])
    cancelled_at = booking_data.get("cancelled_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))

    tickets_html = ""
    for i, ticket in enumerate(tickets):
        tickets_html += (
            f"<div><strong style='text-decoration: line-through'>Passenger {i+1}: {ticket.get('passenger_name','N/A')}</strong><br>"
            f"{ticket.get('flight_number','')} | {ticket.get('route','')} | Seat: {ticket.get('seat_number','N/A')} ({ticket.get('seat_class','Economy')})</div>"
        )

    payload = {
        "recipients": [
            {
                "to": [{"email": to_email, "name": recipient_name or ""}],
                "variables": {
                    "pnr": pnr,
                    "refund_amount": f"{refund_amount:.2f}",
                    "total_fare": f"{total_fare:.2f}",
                    "cancelled_at": cancelled_at,
                    "tickets_html": tickets_html,
                },
            }
        ],
        "from": {"name": "FlightBooker", "email": f"no-reply@{SENDER_DOMAIN}"},
        "domain": SENDER_DOMAIN,
        "template_id": "flightbooker_cancel",
    }

    return _send_msg91(payload)
