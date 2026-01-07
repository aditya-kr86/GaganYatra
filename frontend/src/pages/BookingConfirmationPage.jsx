import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import api from '../api/config';
import {
  CheckCircle, Plane, Download, Printer, Calendar, Clock,
  MapPin, User, CreditCard, AlertCircle, Loader2, Copy,
  Home, FileText, Share2, XCircle, RefreshCw
} from 'lucide-react';
import './BookingConfirmationPage.css';

const BookingConfirmationPage = () => {
  const { pnr } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [booking, setBooking] = useState(location.state?.booking || null);
  const [loading, setLoading] = useState(!location.state?.booking);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Fetch booking if not passed via state
  useEffect(() => {
    const fetchBooking = async () => {
      if (booking) return;
      
      try {
        const response = await api.get(`/bookings/${pnr}`);
        setBooking(response.data);
      } catch (err) {
        setError('Failed to load booking details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchBooking();
  }, [pnr, booking]);

  // Copy PNR to clipboard
  const handleCopyPNR = async () => {
    try {
      await navigator.clipboard.writeText(booking.pnr);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Download PDF ticket
  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await api.get(`/bookings/${pnr}/receipt/pdf`, {
        responseType: 'blob',
      });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `FlightBooker_Ticket_${pnr}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
      alert('Failed to download ticket. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  // Print ticket
  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="confirmation-page">
        <Navbar />
        <div className="confirmation-loading">
          <Loader2 className="spinner" size={48} />
          <p>Loading your booking...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="confirmation-page">
        <Navbar />
        <div className="confirmation-error">
          <AlertCircle size={64} />
          <h2>Booking Not Found</h2>
          <p>{error || 'Unable to load booking details'}</p>
          <Link to="/my-bookings" className="btn btn-primary">
            View My Bookings
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  const firstTicket = booking.tickets?.[0];
  const isCancelled = booking.status?.toLowerCase() === 'cancelled';
  const isConfirmed = booking.status?.toLowerCase() === 'confirmed';

  // Render cancelled booking view
  if (isCancelled) {
    return (
      <div className="confirmation-page">
        <Navbar />
        <main className="confirmation-main">
          <div className="confirmation-container">
            {/* Cancelled Header */}
            <div className="success-header cancelled-header">
              <div className="success-icon cancelled-icon">
                <XCircle size={64} />
              </div>
              <h1>Booking Cancelled</h1>
              <p>This booking has been cancelled. If eligible, a refund will be processed to your original payment method.</p>
            </div>

            {/* PNR Card - Cancelled Style */}
            <div className="pnr-card cancelled">
              <div className="pnr-content">
                <span className="pnr-label">Cancelled Booking Reference</span>
                <div className="pnr-value cancelled-pnr">
                  <span>{booking.pnr}</span>
                </div>
              </div>
            </div>

            {/* Cancelled Ticket Details */}
            <div class="ticket-card cancelled-ticket" id="printable-ticket">
              <div className="ticket-header">
                <div className="ticket-logo">
                  <Plane size={28} />
                  <span>FlightBooker</span>
                </div>
                <div className="ticket-status">
                  <span className="status-badge cancelled">
                    Cancelled
                  </span>
                </div>
              </div>

              {/* Flight Details */}
              <div className="ticket-flight cancelled-flight">
                <div className="flight-info">
                  <span className="flight-number">{firstTicket?.flight_number}</span>
                  <span className="airline">{firstTicket?.airline_name}</span>
                </div>

                <div className="flight-route">
                  <div className="route-city departure">
                    <span className="time">
                      {new Date(firstTicket?.departure_time).toLocaleTimeString('en-IN', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="city">{firstTicket?.departure_city}</span>
                    <span className="airport">{firstTicket?.departure_airport}</span>
                  </div>

                  <div className="route-visual">
                    <div className="route-line">
                      <div className="dot start"></div>
                      <div className="line"></div>
                      <XCircle size={20} className="plane-icon cancelled-plane" />
                      <div className="line"></div>
                      <div className="dot end"></div>
                    </div>
                    <span className="route-text">{firstTicket?.route}</span>
                  </div>

                  <div className="route-city arrival">
                    <span className="time">
                      {new Date(firstTicket?.arrival_time).toLocaleTimeString('en-IN', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="city">{firstTicket?.arrival_city}</span>
                    <span className="airport">{firstTicket?.arrival_airport}</span>
                  </div>
                </div>
              </div>

              {/* Divider */}
              <div className="ticket-divider">
                <div className="tear left"></div>
                <div className="divider-line"></div>
                <div className="tear right"></div>
              </div>

              {/* Passenger Details */}
              <div className="ticket-passengers cancelled-passengers">
                <h3>Cancelled Passengers</h3>
                <div className="passengers-grid">
                  {booking.tickets?.map((ticket, index) => (
                    <div key={index} className="passenger-item cancelled-passenger">
                      <div className="passenger-icon">
                        <User size={20} />
                      </div>
                      <div className="passenger-details">
                        <span className="name">{ticket.passenger_name}</span>
                        <span className="meta">
                          {ticket.passenger_age} yrs • {ticket.passenger_gender === 'M' ? 'Male' : ticket.passenger_gender === 'F' ? 'Female' : 'Other'}
                        </span>
                        <span className="seat">
                          Seat: {ticket.flight_seat || ticket.seat_number || 'N/A'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cancellation Summary */}
              <div className="ticket-summary cancellation-summary">
                <div className="summary-row">
                  <span className="label">Booking Reference</span>
                  <span className="value">{booking.booking_reference}</span>
                </div>
                <div className="summary-row">
                  <span className="label">Status</span>
                  <span className="value cancelled-status">
                    <XCircle size={14} />
                    Cancelled
                  </span>
                </div>
                <div className="summary-row">
                  <span className="label">Original Fare</span>
                  <span className="value">₹{booking.total_fare?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="summary-row">
                  <span className="label">Refund Status</span>
                  <span className="value refund-status">
                    <RefreshCw size={14} />
                    Processing (5-7 business days)
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <Link to="/" className="quick-action">
                <Home size={24} />
                <span>Home</span>
              </Link>
              <Link to="/my-bookings" className="quick-action">
                <FileText size={24} />
                <span>My Bookings</span>
              </Link>
              <Link to="/flights" className="quick-action">
                <Plane size={24} />
                <span>Book New Flight</span>
              </Link>
            </div>

            {/* Refund Information */}
            <div className="important-info refund-info">
              <h3>Refund Information</h3>
              <ul>
                <li>Your refund will be processed within 5-7 business days.</li>
                <li>The refund will be credited to your original payment method.</li>
                <li>For any queries regarding refund, please contact our support team.</li>
                <li>You can track your refund status in the My Bookings section.</li>
              </ul>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="confirmation-page">
      <Navbar />

      <main className="confirmation-main">
        <div className="confirmation-container">
          {/* Success Header */}
          <div className="success-header">
            <div className="success-icon">
              <CheckCircle size={64} />
            </div>
            <h1>Booking Confirmed!</h1>
            <p>Your flight has been successfully booked. A confirmation email has been sent.</p>
          </div>

          {/* PNR Card */}
          <div className="pnr-card">
            <div className="pnr-content">
              <span className="pnr-label">Your PNR / Booking Reference</span>
              <div className="pnr-value">
                <span>{booking.pnr}</span>
                <button 
                  className="copy-btn"
                  onClick={handleCopyPNR}
                  title="Copy PNR"
                >
                  {copied ? <CheckCircle size={18} /> : <Copy size={18} />}
                </button>
              </div>
            </div>
            <div className="pnr-actions">
              <button 
                className="action-btn"
                onClick={handleDownloadPDF}
                disabled={downloading}
              >
                {downloading ? (
                  <>
                    <Loader2 className="spinner" size={18} />
                    Downloading...
                  </>
                ) : (
                  <>
                    <Download size={18} />
                    Download Ticket
                  </>
                )}
              </button>
              <button className="action-btn" onClick={handlePrint}>
                <Printer size={18} />
                Print
              </button>
            </div>
          </div>

          {/* Ticket Card */}
          <div className="ticket-card" id="printable-ticket">
            <div className="ticket-header">
              <div className="ticket-logo">
                <Plane size={28} />
                <span>FlightBooker</span>
              </div>
              <div className="ticket-status">
                <span className={`status-badge ${booking.status.toLowerCase()}`}>
                  {booking.status}
                </span>
              </div>
            </div>

            {/* Flight Details */}
            <div className="ticket-flight">
              <div className="flight-info">
                <span className="flight-number">{firstTicket?.flight_number}</span>
                <span className="airline">{firstTicket?.airline_name}</span>
              </div>

              <div className="flight-route">
                <div className="route-city departure">
                  <span className="time">
                    {new Date(firstTicket?.departure_time).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="city">{firstTicket?.departure_city}</span>
                  <span className="airport">{firstTicket?.departure_airport}</span>
                  <span className="date">
                    {new Date(firstTicket?.departure_time).toLocaleDateString('en-IN', {
                      weekday: 'short',
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </span>
                </div>

                <div className="route-visual">
                  <div className="route-line">
                    <div className="dot start"></div>
                    <div className="line"></div>
                    <Plane size={20} className="plane-icon" />
                    <div className="line"></div>
                    <div className="dot end"></div>
                  </div>
                  <span className="route-text">{firstTicket?.route}</span>
                </div>

                <div className="route-city arrival">
                  <span className="time">
                    {new Date(firstTicket?.arrival_time).toLocaleTimeString('en-IN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <span className="city">{firstTicket?.arrival_city}</span>
                  <span className="airport">{firstTicket?.arrival_airport}</span>
                  <span className="date">
                    {new Date(firstTicket?.arrival_time).toLocaleDateString('en-IN', {
                      weekday: 'short',
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            </div>

            {/* Divider with tear effect */}
            <div className="ticket-divider">
              <div className="tear left"></div>
              <div className="divider-line"></div>
              <div className="tear right"></div>
            </div>

            {/* Passenger Details */}
            <div className="ticket-passengers">
              <h3>Passenger Details</h3>
              <div className="passengers-grid">
                {booking.tickets?.map((ticket, index) => (
                  <div key={index} className="passenger-item">
                    <div className="passenger-icon">
                      <User size={20} />
                    </div>
                    <div className="passenger-details">
                      <span className="name">{ticket.passenger_name}</span>
                      <span className="meta">
                        {ticket.passenger_age} yrs • {ticket.passenger_gender === 'M' ? 'Male' : ticket.passenger_gender === 'F' ? 'Female' : 'Other'}
                      </span>
                      <span className="seat">
                        Seat: {ticket.flight_seat || ticket.seat_number || 'To be assigned'}
                      </span>
                      <span className="class">{ticket.seat_class}</span>
                    </div>
                    {ticket.ticket_number && (
                      <div className="ticket-number">
                        <span className="label">Ticket #</span>
                        <span className="value">{ticket.ticket_number}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Booking Summary */}
            <div className="ticket-summary">
              <div className="summary-row">
                <span className="label">Booking Reference</span>
                <span className="value">{booking.booking_reference}</span>
              </div>
              <div className="summary-row">
                <span className="label">PNR</span>
                <span className="value highlight">{booking.pnr}</span>
              </div>
              <div className="summary-row">
                <span className="label">Booked On</span>
                <span className="value">
                  {new Date(booking.created_at).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
              <div className="summary-row">
                <span className="label">Payment Status</span>
                <span className="value paid">
                  <CheckCircle size={14} />
                  Paid ₹{booking.paid_amount?.toFixed(2) || booking.total_fare?.toFixed(2)}
                </span>
              </div>
              {booking.transaction_id && (
                <div className="summary-row">
                  <span className="label">Transaction ID</span>
                  <span className="value">{booking.transaction_id}</span>
                </div>
              )}
            </div>

            {/* Ticket Footer */}
            <div className="ticket-footer">
              <div className="barcode">
                <div className="barcode-lines">
                  {Array.from({ length: 40 }).map((_, i) => (
                    <div 
                      key={i} 
                      className="bar" 
                      style={{ 
                        width: Math.random() > 0.5 ? '3px' : '1px',
                        height: '40px'
                      }}
                    ></div>
                  ))}
                </div>
                <span className="barcode-text">{booking.pnr}</span>
              </div>
              <div className="footer-note">
                <p>Please arrive at the airport at least 2 hours before departure.</p>
                <p>Carry a valid photo ID for verification.</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            <Link to="/" className="quick-action">
              <Home size={24} />
              <span>Home</span>
            </Link>
            <Link to="/my-bookings" className="quick-action">
              <FileText size={24} />
              <span>My Bookings</span>
            </Link>
            <button 
              className="quick-action"
              onClick={handleDownloadPDF}
              disabled={downloading}
            >
              {downloading ? (
                <Loader2 className="spinner" size={24} />
              ) : (
                <Download size={24} />
              )}
              <span>{downloading ? 'Downloading...' : 'Download'}</span>
            </button>
          </div>

          {/* Important Info */}
          <div className="important-info">
            <h3>Important Information</h3>
            <ul>
              <li>Please arrive at the airport at least 2 hours before domestic flights and 3 hours before international flights.</li>
              <li>Carry a valid government-issued photo ID (Aadhaar, Passport, Driving License, etc.)</li>
              <li>Web check-in opens 48 hours before departure and closes 1 hour before.</li>
              <li>For any changes or cancellations, please visit My Bookings or contact our 24/7 support.</li>
            </ul>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default BookingConfirmationPage;
