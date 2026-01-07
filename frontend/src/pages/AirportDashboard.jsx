import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import './AirportDashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function AirportDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('departures');
  const [departures, setDepartures] = useState([]);
  const [arrivals, setArrivals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Gate assignment modal
  const [showGateModal, setShowGateModal] = useState(false);
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [gateAssignment, setGateAssignment] = useState({
    departure_gate: '',
    arrival_gate: '',
    remarks: ''
  });

  useEffect(() => {
    if (!user || user.role !== 'airport_authority') {
      navigate('/login');
      return;
    }
    fetchDashboard();
    fetchFIDS();
  }, [user, navigate]);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/airport-authority/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch dashboard');
      const data = await res.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchFIDS = async () => {
    setLoading(true);
    try {
      const [depRes, arrRes] = await Promise.all([
        fetch(`${API_BASE}/airport-authority/fids/departures`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/airport-authority/fids/arrivals`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      if (!depRes.ok || !arrRes.ok) throw new Error('Failed to fetch FIDS');
      
      const depData = await depRes.json();
      const arrData = await arrRes.json();
      
      setDepartures(depData);
      setArrivals(arrData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchDashboard(), fetchFIDS()]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const openGateModal = (flight) => {
    setSelectedFlight(flight);
    setGateAssignment({
      departure_gate: flight.flight_type === 'Departure' ? (flight.gate || '') : '',
      arrival_gate: flight.flight_type === 'Arrival' ? (flight.gate || '') : '',
      remarks: flight.remarks || ''
    });
    setShowGateModal(true);
  };

  const assignGate = async () => {
    try {
      const res = await fetch(`${API_BASE}/airport-authority/flights/${selectedFlight.id}/gate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(gateAssignment)
      });
      if (!res.ok) throw new Error('Failed to assign gate');
      
      setShowGateModal(false);
      fetchFIDS();
      fetchDashboard();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      'Scheduled': 'status-scheduled',
      'Boarding': 'status-boarding',
      'Delayed': 'status-delayed',
      'Departed': 'status-departed',
      'Landed': 'status-landed',
      'Cancelled': 'status-cancelled'
    };
    return classes[status] || 'status-scheduled';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'Scheduled': '🕐',
      'Boarding': '🚶',
      'Delayed': '⚠️',
      'Departed': '✈️',
      'Landed': '✅',
      'Cancelled': '❌'
    };
    return icons[status] || '🕐';
  };

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short'
    });
  };

  const getCurrentTime = () => {
    return new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const getCurrentDate = () => {
    return new Date().toLocaleDateString('en-IN', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  const [currentTime, setCurrentTime] = useState(getCurrentTime());
  const [currentDate, setCurrentDate] = useState(getCurrentDate());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(getCurrentTime());
      setCurrentDate(getCurrentDate());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const autoRefresh = setInterval(() => {
      fetchFIDS();
    }, 30000);
    return () => clearInterval(autoRefresh);
  }, []);

  if (!user || user.role !== 'airport_authority') {
    return (
      <div className="access-denied">
        <div className="access-denied-content">
          <span className="access-icon">🔒</span>
          <h2>Access Denied</h2>
          <p>You don't have permission to view this page</p>
          <Link to="/login" className="login-link">Go to Login</Link>
        </div>
      </div>
    );
  }

  const activeFlights = activeTab === 'departures' ? departures : arrivals;
  const boardingCount = activeFlights.filter(f => f.status === 'Boarding').length;
  const delayedCount = activeFlights.filter(f => f.status === 'Delayed').length;

  return (
    <div className="airport-dashboard">
      {/* Animated Background */}
      <div className="dashboard-bg">
        <div className="bg-gradient"></div>
        <div className="bg-grid"></div>
      </div>

      {/* Header / Navbar */}
      <header className="dashboard-header">
        <div className="header-container">
          {/* Left Section - Airport Brand */}
          <div className="header-left">
            <div className="airport-brand">
              <div className="airport-logo">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                </svg>
              </div>
              <div className="airport-info">
                <h1>{stats?.airport_name || 'Airport Authority'}</h1>
                <div className="airport-meta">
                  <span className="airport-code">{stats?.airport_code || 'IATA'}</span>
                  <span className="meta-separator"></span>
                  <span className="city">{stats?.city || 'City'}, India</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Center Section - Live Clock */}
          <div className="header-center">
            <div className="live-clock">
              <div className="clock-time">
                <span className="time-digits">{currentTime}</span>
                <span className="time-zone-badge">IST</span>
              </div>
              <div className="clock-date">{currentDate}</div>
            </div>
          </div>

          {/* Right Section - Action Buttons */}
          <div className="header-right">
            <div className="header-actions">
              <button 
                onClick={handleRefresh} 
                className={`nav-action-btn refresh-btn ${isRefreshing ? 'spinning' : ''}`}
                title="Refresh Data"
              >
                <div className="btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M23 4v6h-6M1 20v-6h6"/>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                  </svg>
                </div>
                <span className="btn-label">Refresh</span>
              </button>

              <Link to="/" className="nav-action-btn home-btn" title="Home">
                <div className="btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                    <polyline points="9,22 9,12 15,12 15,22"/>
                  </svg>
                </div>
                <span className="btn-label">Home</span>
              </Link>

              <button 
                onClick={() => { logout(); navigate('/login'); }} 
                className="nav-action-btn logout-btn"
                title="Logout"
              >
                <div className="btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16,17 21,12 16,7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                </div>
                <span className="btn-label">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{error}</span>
          <button onClick={() => setError('')}>✕</button>
        </div>
      )}

      {/* Stats Dashboard */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card primary departures-card">
            <div className="stat-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats?.total_departures_today || 0}</span>
              <span className="stat-label">Departures Today</span>
            </div>
            <div className="stat-trend up">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"/>
                <polyline points="17,6 23,6 23,12"/>
              </svg>
            </div>
          </div>

          <div className="stat-card primary arrivals-card">
            <div className="stat-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 22h20M3 10h4l4 8 4-12 4 4h2"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats?.total_arrivals_today || 0}</span>
              <span className="stat-label">Arrivals Today</span>
            </div>
            <div className="stat-trend up">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"/>
                <polyline points="17,6 23,6 23,12"/>
              </svg>
            </div>
          </div>

          <div className="stat-card ontime-card">
            <div className="stat-icon-wrapper success">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22,4 12,14.01 9,11.01"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{(stats?.on_time_departures || 0) + (stats?.on_time_arrivals || 0)}</span>
              <span className="stat-label">On Time</span>
            </div>
          </div>

          <div className="stat-card delayed-card">
            <div className="stat-icon-wrapper warning">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12,6 12,12 16,14"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{(stats?.delayed_departures || 0) + (stats?.delayed_arrivals || 0)}</span>
              <span className="stat-label">Delayed</span>
            </div>
          </div>

          <div className="stat-card cancelled-card">
            <div className="stat-icon-wrapper danger">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats?.cancelled_flights || 0}</span>
              <span className="stat-label">Cancelled</span>
            </div>
          </div>

          <div className="stat-card gates-card">
            <div className="stat-icon-wrapper info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
              </svg>
            </div>
            <div className="stat-content">
              <span className="stat-value">{stats?.gates_in_use || 0}</span>
              <span className="stat-label">Gates Active</span>
            </div>
          </div>
        </div>
      </section>
      {/* Stats Dashboard */}
      <section className="fids-section">
        <div className="fids-header">
          <div className="fids-title">
            <div className="fids-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
            </div>
            <div>
              <h2>Flight Information Display System</h2>
              <p className="fids-subtitle">Real-time flight status • Auto-refresh every 30s</p>
            </div>
          </div>
          
          <div className="fids-controls">
            <div className="live-indicator">
              <span className="live-dot"></span>
              <span>LIVE</span>
            </div>
            <div className="fids-tabs">
              <button 
                className={`tab-btn ${activeTab === 'departures' ? 'active' : ''}`}
                onClick={() => setActiveTab('departures')}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                </svg>
                <span>Departures</span>
                <span className="tab-count">{departures.length}</span>
              </button>
              <button 
                className={`tab-btn ${activeTab === 'arrivals' ? 'active' : ''}`}
                onClick={() => setActiveTab('arrivals')}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{transform: 'rotate(180deg) scaleX(-1)'}}>
                  <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                </svg>
                <span>Arrivals</span>
                <span className="tab-count">{arrivals.length}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="fids-quick-stats">
          <div className="quick-stat">
            <span className="quick-stat-icon boarding">🚶</span>
            <span className="quick-stat-value">{boardingCount}</span>
            <span className="quick-stat-label">Boarding Now</span>
          </div>
          <div className="quick-stat">
            <span className="quick-stat-icon delayed">⚠️</span>
            <span className="quick-stat-value">{delayedCount}</span>
            <span className="quick-stat-label">Delayed</span>
          </div>
          <div className="quick-stat">
            <span className="quick-stat-icon total">✈️</span>
            <span className="quick-stat-value">{activeFlights.length}</span>
            <span className="quick-stat-label">Total {activeTab}</span>
          </div>
        </div>
        
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <span>Loading flight information...</span>
          </div>
        ) : (
          <div className="fids-board">
            <div className="fids-table-container">
              <table className="fids-table">
                <thead>
                  <tr>
                    <th>
                      <span className="th-content">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                          <circle cx="12" cy="12" r="10"/>
                          <polyline points="12,6 12,12 16,14"/>
                        </svg>
                        Time
                      </span>
                    </th>
                    <th>Flight</th>
                    <th>Airline</th>
                    <th>{activeTab === 'departures' ? 'Destination' : 'Origin'}</th>
                    <th>
                      <span className="th-content">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                          <line x1="9" y1="3" x2="9" y2="21"/>
                        </svg>
                        Gate
                      </span>
                    </th>
                    <th>Status</th>
                    <th>Remarks</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {activeFlights.map((flight, index) => (
                    <tr 
                      key={flight.id} 
                      className={`flight-row ${getStatusBadgeClass(flight.status)}`}
                      style={{'--row-index': index}}
                    >
                      <td className="time-col">
                        <div className="time-display">
                          <span className="scheduled-time">{formatTime(flight.scheduled_time)}</span>
                          <span className="date-badge">{formatDate(flight.scheduled_time)}</span>
                        </div>
                        {flight.estimated_time && flight.delay_minutes > 0 && (
                          <div className="estimated-time">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                              <circle cx="12" cy="12" r="3"/>
                            </svg>
                            {formatTime(flight.estimated_time)}
                          </div>
                        )}
                      </td>
                      <td className="flight-col">
                        <span className="flight-number">{flight.flight_number}</span>
                      </td>
                      <td className="airline-col">
                        <div className="airline-info">
                          <span className="airline-code">{flight.airline_code}</span>
                          <span className="airline-name">{flight.airline_name}</span>
                        </div>
                      </td>
                      <td className="city-col">
                        <div className="city-info">
                          <span className="city-code">
                            {activeTab === 'departures' ? flight.destination_code : flight.origin_code}
                          </span>
                          <span className="city-name">
                            {activeTab === 'departures' ? flight.destination_city : flight.origin_city}
                          </span>
                        </div>
                      </td>
                      <td className="gate-col">
                        <span className={`gate-number ${flight.gate ? 'assigned' : 'pending'}`}>
                          {flight.gate || '—'}
                        </span>
                      </td>
                      <td className="status-col">
                        <div className="status-wrapper">
                          <span className={`fids-status-badge ${getStatusBadgeClass(flight.status)}`}>
                            <span className="status-icon">{getStatusIcon(flight.status)}</span>
                            <span>{flight.status}</span>
                          </span>
                          {flight.delay_minutes > 0 && (
                            <span className="delay-badge">+{flight.delay_minutes}m</span>
                          )}
                        </div>
                      </td>
                      <td className="remarks-col">
                        <span className="remarks-text">{flight.remarks || '—'}</span>
                      </td>
                      <td className="actions-col">
                        <button 
                          onClick={() => openGateModal(flight)}
                          className="gate-action-btn"
                          title="Assign/Update Gate"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                            <line x1="9" y1="3" x2="9" y2="21"/>
                          </svg>
                          <span>Gate</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {activeFlights.length === 0 && (
                <div className="no-flights">
                  <div className="no-flights-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                    </svg>
                  </div>
                  <h3>No {activeTab} scheduled</h3>
                  <p>There are no {activeTab === 'departures' ? 'departing' : 'arriving'} flights at this time</p>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Gate Assignment Modal */}
      {showGateModal && selectedFlight && (
        <div className="modal-overlay" onClick={() => setShowGateModal(false)}>
          <div className="modal-content gate-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="9" y1="3" x2="9" y2="21"/>
                </svg>
              </div>
              <div>
                <h3>Assign Gate</h3>
                <p>Update gate assignment for this flight</p>
              </div>
              <button className="modal-close" onClick={() => setShowGateModal(false)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div className="flight-info-card">
              <div className="flight-info-header">
                <span className="flight-number-large">{selectedFlight.flight_number}</span>
                <span className={`status-pill ${getStatusBadgeClass(selectedFlight.status)}`}>
                  {selectedFlight.status}
                </span>
              </div>
              <div className="flight-info-details">
                <div className="detail-item">
                  <span className="detail-label">Type</span>
                  <span className="detail-value">{selectedFlight.flight_type}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Time</span>
                  <span className="detail-value">{formatTime(selectedFlight.scheduled_time)}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">
                    {selectedFlight.flight_type === 'Departure' ? 'To' : 'From'}
                  </span>
                  <span className="detail-value">
                    {selectedFlight.flight_type === 'Departure' ? 
                      `${selectedFlight.destination_city} (${selectedFlight.destination_code})` :
                      `${selectedFlight.origin_city} (${selectedFlight.origin_code})`
                    }
                  </span>
                </div>
              </div>
            </div>
            
            <div className="form-section">
              <div className="form-group">
                <label>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="9" y1="3" x2="9" y2="21"/>
                  </svg>
                  {selectedFlight.flight_type === 'Departure' ? 'Departure Gate' : 'Arrival Gate'}
                </label>
                <input
                  type="text"
                  value={selectedFlight.flight_type === 'Departure' ? 
                    gateAssignment.departure_gate : gateAssignment.arrival_gate}
                  onChange={(e) => {
                    if (selectedFlight.flight_type === 'Departure') {
                      setGateAssignment({...gateAssignment, departure_gate: e.target.value.toUpperCase()});
                    } else {
                      setGateAssignment({...gateAssignment, arrival_gate: e.target.value.toUpperCase()});
                    }
                  }}
                  placeholder="e.g., A12, T2-G5, 23"
                  maxLength={10}
                  className="gate-input"
                />
              </div>
              
              <div className="form-group">
                <label>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                  Remarks (optional)
                </label>
                <input
                  type="text"
                  value={gateAssignment.remarks}
                  onChange={(e) => setGateAssignment({...gateAssignment, remarks: e.target.value})}
                  placeholder="Any additional notes..."
                />
              </div>
            </div>
            
            <div className="modal-actions">
              <button onClick={() => setShowGateModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={assignGate} className="btn-primary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
                Assign Gate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AirportDashboard;
