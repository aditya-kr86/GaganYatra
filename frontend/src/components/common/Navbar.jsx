import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plane, Menu, X, User, LogOut, Settings, Ticket, ChevronDown, Search, AlertCircle, Clock, MapPin, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import api from '../../api/config';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isPnrModalOpen, setIsPnrModalOpen] = useState(false);
  const [pnrInput, setPnrInput] = useState('');
  const [pnrStatus, setPnrStatus] = useState(null);
  const [pnrLoading, setPnrLoading] = useState(false);
  const [pnrError, setPnrError] = useState('');
  const dropdownRef = useRef(null);
  const pnrModalRef = useRef(null);
  const { user, isAuthenticated, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const toggleDropdown = () => setIsDropdownOpen(!isDropdownOpen);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
      if (pnrModalRef.current && !pnrModalRef.current.contains(event.target)) {
        // Don't close if clicking the button that opens the modal
        if (!event.target.closest('.pnr-check-btn')) {
          setIsPnrModalOpen(false);
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    setIsDropdownOpen(false);
    setIsMenuOpen(false);
    navigate('/');
  };

  const handlePnrCheck = async (e) => {
    e.preventDefault();
    if (!pnrInput.trim()) {
      setPnrError('Please enter a PNR number');
      return;
    }
    
    setPnrLoading(true);
    setPnrError('');
    setPnrStatus(null);
    
    try {
      const response = await api.get(`/bookings/pnr-status/${pnrInput.trim().toUpperCase()}`);
      setPnrStatus(response.data);
    } catch (err) {
      setPnrError(err.response?.data?.detail || 'PNR not found. Please check and try again.');
    } finally {
      setPnrLoading(false);
    }
  };

  const closePnrModal = () => {
    setIsPnrModalOpen(false);
    setPnrInput('');
    setPnrStatus(null);
    setPnrError('');
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return '#10b981';
      case 'cancelled': return '#ef4444';
      case 'pending': return '#f59e0b';
      case 'payment pending': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <Plane className="logo-icon" />
          <span className="logo-text">FlightBooker</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="navbar-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/flights" className="nav-link">Flights</Link>
          <button className="nav-link pnr-check-btn" onClick={() => setIsPnrModalOpen(true)}>
            <Search size={16} />
            PNR Status
          </button>
          {isAuthenticated() && (
            <Link to="/my-bookings" className="nav-link">My Bookings</Link>
          )}
          <Link to="/about" className="nav-link">About</Link>
          {isAdmin() && (
            <Link to="/admin/dashboard" className="nav-link admin-link">Admin</Link>
          )}
        </div>

        {/* Auth Buttons / User Menu */}
        <div className="navbar-auth">
          {isAuthenticated() ? (
            <div className="user-menu" ref={dropdownRef}>
              <button className="user-menu-btn" onClick={toggleDropdown}>
                <div className="user-avatar">
                  <User size={18} />
                </div>
                <span className="user-name">{user?.first_name}</span>
                <ChevronDown size={16} className={`dropdown-arrow ${isDropdownOpen ? 'open' : ''}`} />
              </button>
              
              {isDropdownOpen && (
                <div className="user-dropdown">
                  <div className="dropdown-header">
                    <span className="dropdown-name">{user?.first_name} {user?.last_name}</span>
                    <span className="dropdown-email">{user?.email}</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <Link to="/profile" className="dropdown-item" onClick={() => setIsDropdownOpen(false)}>
                    <Settings size={16} />
                    Profile Settings
                  </Link>
                  <Link to="/my-bookings" className="dropdown-item" onClick={() => setIsDropdownOpen(false)}>
                    <Ticket size={16} />
                    My Bookings
                  </Link>
                  {isAdmin() && (
                    <Link to="/admin/dashboard" className="dropdown-item" onClick={() => setIsDropdownOpen(false)}>
                      <User size={16} />
                      Admin Dashboard
                    </Link>
                  )}
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item logout" onClick={handleLogout}>
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline">
                <User size={18} />
                Login
              </Link>
              <Link to="/register" className="btn btn-primary">
                Sign Up
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button className="mobile-menu-btn" onClick={toggleMenu}>
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="mobile-menu">
          <Link to="/" className="mobile-link" onClick={toggleMenu}>Home</Link>
          <Link to="/flights" className="mobile-link" onClick={toggleMenu}>Flights</Link>
          <button className="mobile-link pnr-check-btn" onClick={() => { toggleMenu(); setIsPnrModalOpen(true); }}>
            <Search size={16} />
            PNR Status
          </button>
          {isAuthenticated() && (
            <Link to="/my-bookings" className="mobile-link" onClick={toggleMenu}>My Bookings</Link>
          )}
          <Link to="/about" className="mobile-link" onClick={toggleMenu}>About</Link>
          {isAdmin() && (
            <Link to="/admin/dashboard" className="mobile-link" onClick={toggleMenu}>Admin Dashboard</Link>
          )}
          <div className="mobile-auth">
            {isAuthenticated() ? (
              <>
                <Link to="/profile" className="btn btn-outline" onClick={toggleMenu}>
                  <Settings size={18} />
                  Profile
                </Link>
                <button className="btn btn-primary" onClick={handleLogout}>
                  <LogOut size={18} />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline" onClick={toggleMenu}>Login</Link>
                <Link to="/register" className="btn btn-primary" onClick={toggleMenu}>Sign Up</Link>
              </>
            )}
          </div>
        </div>
      )}

      {/* PNR Status Modal */}
      {isPnrModalOpen && (
        <div className="pnr-modal-overlay">
          <div className="pnr-modal" ref={pnrModalRef}>
            <div className="pnr-modal-header">
              <h3><Search size={20} /> Check PNR Status</h3>
              <button className="pnr-modal-close" onClick={closePnrModal}>
                <X size={20} />
              </button>
            </div>
            
            <form onSubmit={handlePnrCheck} className="pnr-search-form">
              <div className="pnr-input-group">
                <input
                  type="text"
                  placeholder="Enter PNR Number (e.g., ABC123)"
                  value={pnrInput}
                  onChange={(e) => setPnrInput(e.target.value.toUpperCase())}
                  className="pnr-input"
                  maxLength={10}
                  autoFocus
                />
                <button type="submit" className="pnr-search-btn" disabled={pnrLoading}>
                  {pnrLoading ? <Loader2 size={18} className="spin" /> : <Search size={18} />}
                  {pnrLoading ? 'Checking...' : 'Check Status'}
                </button>
              </div>
            </form>

            {pnrError && (
              <div className="pnr-error">
                <AlertCircle size={16} />
                {pnrError}
              </div>
            )}

            {pnrStatus && (
              <div className="pnr-result">
                <div className="pnr-result-header">
                  <div className="pnr-number">
                    <span className="label">PNR</span>
                    <span className="value">{pnrStatus.pnr}</span>
                  </div>
                  <div className="pnr-status" style={{ backgroundColor: getStatusColor(pnrStatus.status) }}>
                    {pnrStatus.status}
                  </div>
                </div>

                <div className="pnr-tickets">
                  {pnrStatus.tickets.map((ticket, index) => (
                    <div key={index} className="pnr-ticket-card">
                      <div className="ticket-passenger">
                        <User size={16} />
                        <span>{ticket.passenger_name}</span>
                      </div>
                      
                      <div className="ticket-flight-info">
                        <div className="flight-number">
                          <Plane size={16} />
                          <span>{ticket.flight_number}</span>
                        </div>
                        <div className="flight-route">
                          <MapPin size={16} />
                          <span>{ticket.route}</span>
                        </div>
                      </div>

                      <div className="ticket-details">
                        <div className="detail-item">
                          <Clock size={14} />
                          <span>{ticket.departure_date} at {ticket.departure_time}</span>
                        </div>
                        <div className="detail-item">
                          <Ticket size={14} />
                          <span>{ticket.seat_class} {ticket.seat_number ? `- Seat ${ticket.seat_number}` : ''}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
