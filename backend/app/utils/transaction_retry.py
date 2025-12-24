"""
Transactional retry utilities for handling concurrent booking conflicts.
"""
import time
import functools
from sqlalchemy.exc import OperationalError, DBAPIError
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def retry_on_deadlock(max_retries: int = 3, initial_delay: float = 0.1, backoff_factor: float = 2.0):
    """
    Decorator to retry database operations on deadlock or lock timeout.
    
    Uses exponential backoff to space out retry attempts.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay on each subsequent retry
    
    Example:
        @retry_on_deadlock(max_retries=3)
        def create_booking_with_retry(db, ...):
            return create_booking(db, ...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a deadlock or lock timeout
                    is_retryable = any(keyword in error_msg for keyword in [
                        'deadlock',
                        'lock',
                        'timeout',
                        'database is locked',
                        'could not obtain lock'
                    ])
                    
                    if not is_retryable or attempt >= max_retries:
                        raise
                    
                    # Wait before retrying with exponential backoff
                    time.sleep(delay)
                    delay *= backoff_factor
                    
                    # Log retry attempt (optional)
                    print(f"[Retry] Attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay due to: {e}")
                    
            # Should not reach here, but raise last exception if it does
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def with_transaction_retry(db_session, operation: Callable[[], T], max_retries: int = 3) -> T:
    """
    Execute a database operation with automatic retry on deadlock.
    
    Args:
        db_session: SQLAlchemy session
        operation: Callable that performs the database operation
        max_retries: Maximum number of retry attempts
    
    Returns:
        Result of the operation
        
    Example:
        result = with_transaction_retry(
            db,
            lambda: create_booking(db, user_id, flight_id, date, passengers),
            max_retries=3
        )
    """
    delay = 0.1
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except (OperationalError, DBAPIError) as e:
            last_exception = e
            db_session.rollback()
            
            error_msg = str(e).lower()
            is_retryable = any(keyword in error_msg for keyword in [
                'deadlock',
                'lock',
                'timeout',
                'database is locked',
                'could not obtain lock'
            ])
            
            if not is_retryable or attempt >= max_retries:
                raise
            
            time.sleep(delay)
            delay *= 2.0
            
    if last_exception:
        raise last_exception
