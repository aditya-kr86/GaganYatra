import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/config';
import { 
  Plane, Calendar, MapPin, Clock, Ticket, X, Download, 
  AlertCircle, Loader2, ChevronRight, Filter, Eye
} from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './MyBookingsPage.css';

const MyBookingsPage = () => {
  const { token, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [cancellingId, setCancellingId] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated()) {
      navigate('/login', { state: { from: { pathname: '/my-bookings' } } });
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    const fetchBookings = async () => {
      if (!token) return;
      
      try {
        const response = await api.get('/users/my-bookings', {
          headers: { Authorization: `Bearer ${token}` }
        });
        // API returns { bookings: [...], user_id, user_name, total_bookings }
        setBookings(response.data.bookings || []);
      } catch (err) {
        setError('Failed to load bookings');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchBookings();
    }
  }, [token]);

  const handleCancelBooking = async (pnr) => {
    if (!confirm('Are you sure you want to cancel this booking?')) return;
    
    setCancellingId(pnr);
    try {
      await api.delete(`/bookings/${pnr}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookings(prev => prev.map(b => 
        b.pnr === pnr ? { ...b, status: 'Cancelled' } : b
      ));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel booking');
    } finally {
      setCancellingId(null);
    }
  };

  const handleDownloadTicket = async (pnr) => {
    setDownloadingId(pnr);
    try {
      const response = await api.get(`/bookings/${pnr}/receipt/pdf`, {
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` }
      });
      
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
      alert('Failed to download ticket');
    } finally {
      setDownloadingId(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return 'status-confirmed';
      case 'pending': return 'status-pending';
      case 'cancelled': return 'status-cancelled';
      case 'completed': return 'status-completed';
      default: return '';
    }
  };

  const filteredBookings = bookings.filter(booking => {
    if (filter === 'all') return true;
    return booking.status?.toLowerCase() === filter;
  });

  if (authLoading || loading) {
    return (
      <div className="bookings-loading">
        <Loader2 className="spinner" size={48} />
        <p>Loading your bookings...</p>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="bookings-page">
        <div className="bookings-container">
          <div className="bookings-header">
            <div>
              <h1>My Bookings</h1>
              <p>View and manage your flight bookings</p>
            </div>
            <div className="filter-wrapper">
              <Filter size={18} />
              <select 
                value={filter} 
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="all">All Bookings</option>
                <option value="confirmed">Confirmed</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          {error && (
            <div className="bookings-error">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {filteredBookings.length === 0 ? (
            <div className="no-bookings">
              <Ticket size={64} />
              <h2>No Bookings Found</h2>
              <p>
                {filter === 'all' 
                  ? "You haven't made any bookings yet."
                  : `No ${filter} bookings found.`}
              </p>
              <Link to="/" className="book-now-btn">
                Book a Flight
                <ChevronRight size={18} />
              </Link>
            </div>
          ) : (
            <div className="bookings-list">
              {filteredBookings.map((booking) => {
                const firstTicket = booking.tickets?.[0];
                return (
                <div key={booking.pnr} className="booking-card">
                  <div className="booking-header">
                    <div className="booking-id">
                      <span className="label">PNR</span>
                      <span className="value">{booking.pnr}</span>
                    </div>
                    <span className={`booking-status ${getStatusColor(booking.status)}`}>
                      {booking.status}
                    </span>
                  </div>

                  <div className="booking-content">
                    <div className="flight-info">
                      <div className="route">
                        <div className="city">
                          <MapPin size={16} />
                          <span>{firstTicket?.departure_city || 'Origin'}</span>
                        </div>
                        <div className="route-line">
                          <Plane size={20} />
                        </div>
                        <div className="city">
                          <MapPin size={16} />
                          <span>{firstTicket?.arrival_city || 'Destination'}</span>
                        </div>
                      </div>

                      <div className="flight-details">
                        <div className="detail">
                          <span className="flight-num">{firstTicket?.flight_number}</span>
                        </div>
                        <div className="detail">
                          <Calendar size={16} />
                          <span>
                            {firstTicket?.departure_time 
                              ? new Date(firstTicket.departure_time).toLocaleDateString('en-IN', {
                                  weekday: 'short',
                                  day: 'numeric',
                                  month: 'short'
                                })
                              : 'Date TBD'}
                          </span>
                        </div>
                        <div className="detail">
                          <Clock size={16} />
                          <span>
                            {firstTicket?.departure_time 
                              ? new Date(firstTicket.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                              : 'Time TBD'}
                          </span>
                        </div>
                        <div className="detail">
                          <span className="passengers">
                            {booking.tickets?.length || 1} Passenger(s)
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="booking-price">
                      <span className="label">Total Fare</span>
                      <span className="amount">₹{booking.total_fare?.toLocaleString() || '0'}</span>
                      {booking.paid_amount && (
                        <span className="paid-badge">Paid</span>
                      )}
                    </div>
                  </div>

                  <div className="booking-actions">
                    {booking.status?.toLowerCase() === 'confirmed' && (
                      <>
                        <button 
                          className="action-btn download"
                          onClick={() => handleDownloadTicket(booking.pnr)}
                          disabled={downloadingId === booking.pnr}
                        >
                          {downloadingId === booking.pnr ? (
                            <Loader2 className="spinner" size={16} />
                          ) : (
                            <Download size={16} />
                          )}
                          Download Ticket
                        </button>
                        <button 
                          className="action-btn cancel"
                          onClick={() => handleCancelBooking(booking.pnr)}
                          disabled={cancellingId === booking.pnr}
                        >
                          {cancellingId === booking.pnr ? (
                            <Loader2 className="spinner" size={16} />
                          ) : (
                            <X size={16} />
                          )}
                          Cancel
                        </button>
                      </>
                    )}
                    {booking.status?.toLowerCase() === 'pending' && (
                      <button 
                        className="action-btn cancel"
                        onClick={() => handleCancelBooking(booking.pnr)}
                        disabled={cancellingId === booking.pnr}
                      >
                        {cancellingId === booking.pnr ? (
                          <Loader2 className="spinner" size={16} />
                        ) : (
                          <X size={16} />
                        )}
                        Cancel
                      </button>
                    )}
                    <Link to={`/booking/confirmation/${booking.pnr}`} className="action-btn view">
                      <Eye size={16} />
                      View Details
                    </Link>
                  </div>
                </div>
              )})}
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
};

export default MyBookingsPage;
