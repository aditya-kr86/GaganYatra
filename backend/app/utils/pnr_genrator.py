"""
PNR (Passenger Name Record) generation utility.
"""
from datetime import datetime
import random
import string


def generate_pnr(booking_id: int | None = None, prefix: str = "FB") -> str:
    """
    Generate a unique PNR (Passenger Name Record) identifier.
    
    Format: PREFIX + YY + ALPHANUMERIC (6 chars)
    Example: FB25AB12CD
    
    Args:
        booking_id: Optional booking ID to incorporate
        prefix: PNR prefix (default: FB for FlightBooker)
    
    Returns:
        PNR string (e.g., FB25A1B2C3)
    """
    year_suffix = str(datetime.utcnow().year)[-2:]
    
    if booking_id is not None:
        # Use booking_id with padding
        pnr = f"{prefix}{year_suffix}{booking_id:06d}"
    else:
        # Generate random alphanumeric
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pnr = f"{prefix}{year_suffix}{random_part}"
    
    return pnr.upper()


def validate_pnr(pnr: str) -> bool:
    """
    Validate PNR format.
    
    Args:
        pnr: PNR string to validate
    
    Returns:
        True if valid format, False otherwise
    """
    if not pnr or len(pnr) < 8:
        return False
    
    # Check if alphanumeric
    if not pnr.isalnum():
        return False
    
    # Check if starts with common prefix
    valid_prefixes = ['GJ', 'AI', '6E', 'UK', 'SG']
    starts_valid = any(pnr.upper().startswith(p) for p in valid_prefixes)
    
    return starts_valid
