import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import './AirlineDashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function AirlineDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  
  const [stats, setStats] = useState(null);
  const [flights, setFlights] = useState([]);
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateFilter, setDateFilter] = useState(new Date().toISOString().split('T')[0]);
  const [statusFilter, setStatusFilter] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  
  // Status update modal
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusUpdate, setStatusUpdate] = useState({
    status: '',
    delay_minutes: 0,
    delay_reason: '',
    remarks: ''
  });

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!user || user.role !== 'airline_staff') {
      navigate('/login');
      return;
    }
    fetchDashboard();
    fetchFlights();
  }, [user, navigate]);

  useEffect(() => {
    fetchFlights();
  }, [dateFilter, statusFilter]);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/airline-staff/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch dashboard');
      const data = await res.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchFlights = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/airline-staff/flights`;
      const params = new URLSearchParams();
      if (dateFilter) params.append('date', dateFilter);
      if (statusFilter) params.append('status_filter', statusFilter);
      if (params.toString()) url += `?${params.toString()}`;
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch flights');
      const data = await res.json();
      setFlights(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchManifest = async (flightId) => {
    try {
      const res = await fetch(`${API_BASE}/airline-staff/flights/${flightId}/manifest`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch manifest');
      const data = await res.json();
      setManifest(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const openStatusModal = (flight) => {
    setSelectedFlight(flight);
    setStatusUpdate({
      status: flight.status,
      delay_minutes: flight.delay_minutes || 0,
      delay_reason: flight.delay_reason || '',
      remarks: flight.remarks || ''
    });
    setShowStatusModal(true);
  };

  const updateFlightStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/airline-staff/flights/${selectedFlight.id}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(statusUpdate)
      });
      if (!res.ok) throw new Error('Failed to update status');
      
      setShowStatusModal(false);
      fetchFlights();
      fetchDashboard();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusIcon = (status) => {
    const icons = {
      'Scheduled': '🕐',
      'Boarding': '🚶',
      'Delayed': '⏰',
      'Departed': '🛫',
      'Landed': '🛬',
      'Cancelled': '❌'
    };
    return icons[status] || '📋';
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

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', { 
      weekday: 'short',
      day: 'numeric',
      month: 'short'
    });
  };

  const getOccupancyPercent = (booked, total) => {
    return total > 0 ? Math.round((booked / total) * 100) : 0;
  };

  const getOccupancyColor = (booked, total) => {
    const percent = (booked / total) * 100;
    if (percent >= 90) return '#22c55e';
    if (percent >= 70) return '#84cc16';
    if (percent >= 50) return '#eab308';
    if (percent >= 30) return '#f97316';
    return '#ef4444';
  };

  if (!user || user.role !== 'airline_staff') {
    return <div className="access-denied">Access Denied</div>;
  }

  return (
    <div className="airline-dashboard">
      {/* Modern Header */}
      <header className="dashboard-header">
        <div className="header-brand">
          <div className="brand-icon">✈️</div>
          <div className="brand-info">
            <h1>{stats?.airline_name || 'Airline'}</h1>
            <span className="brand-code">{stats?.airline_code} • Operations Center</span>
          </div>
        </div>
        
        <div className="header-clock">
          <div className="clock-time">
            {currentTime.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
          </div>
          <div className="clock-date">
            {currentTime.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
        </div>

        <div className="header-actions">
          <Link to="/" className="header-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            Home
          </Link>
          <button onClick={() => { fetchDashboard(); fetchFlights(); }} className="header-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
            Refresh
          </button>
          <button onClick={() => { logout(); navigate('/login'); }} className="header-btn logout">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
            Logout
          </button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
          {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Stats Section */}
      {stats && (
        <section className="stats-section">
          <div className="stats-primary">
            <div className="stat-card hero">
              <div className="stat-icon flights">🛫</div>
              <div className="stat-info">
                <span className="stat-number">{stats.total_flights_today}</span>
                <span className="stat-label">Flights Today</span>
              </div>
              <div className="stat-trend">
                <span className="trend-badge">{stats.total_flights_week} this week</span>
              </div>
            </div>

            <div className="stat-card hero">
              <div className="stat-icon passengers">👥</div>
              <div className="stat-info">
                <span className="stat-number">{stats.total_passengers_today}</span>
                <span className="stat-label">Passengers Today</span>
              </div>
            </div>
          </div>

          <div className="stats-status-bar">
            <div className="status-item scheduled">
              <span className="status-count">{stats.scheduled}</span>
              <span className="status-name">🕐 Scheduled</span>
            </div>
            <div className="status-divider"></div>
            <div className="status-item boarding">
              <span className="status-count">{stats.boarding}</span>
              <span className="status-name">🚶 Boarding</span>
            </div>
            <div className="status-divider"></div>
            <div className="status-item delayed">
              <span className="status-count">{stats.delayed}</span>
              <span className="status-name">⏰ Delayed</span>
            </div>
            <div className="status-divider"></div>
            <div className="status-item departed">
              <span className="status-count">{stats.departed}</span>
              <span className="status-name">🛫 Departed</span>
            </div>
            <div className="status-divider"></div>
            <div className="status-item landed">
              <span className="status-count">{stats.landed}</span>
              <span className="status-name">🛬 Landed</span>
            </div>
            <div className="status-divider"></div>
            <div className="status-item cancelled">
              <span className="status-count">{stats.cancelled}</span>
              <span className="status-name">❌ Cancelled</span>
            </div>
          </div>
        </section>
      )}

      {/* Controls Bar */}
      <section className="controls-section">
        <div className="filters-group">
          <div className="filter-item">
            <label>Date</label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label>Status</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              <option value="Scheduled">🕐 Scheduled</option>
              <option value="Boarding">🚶 Boarding</option>
              <option value="Delayed">⏰ Delayed</option>
              <option value="Departed">🛫 Departed</option>
              <option value="Landed">🛬 Landed</option>
              <option value="Cancelled">❌ Cancelled</option>
            </select>
          </div>
        </div>

        <div className="view-toggle">
          <button 
            className={viewMode === 'cards' ? 'active' : ''} 
            onClick={() => setViewMode('cards')}
            title="Card View"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
          </button>
          <button 
            className={viewMode === 'table' ? 'active' : ''} 
            onClick={() => setViewMode('table')}
            title="Table View"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" x2="21" y1="9" y2="9"/><line x1="3" x2="21" y1="15" y2="15"/><line x1="9" x2="9" y1="9" y2="21"/></svg>
          </button>
        </div>

        <div className="flight-count">
          <span className="count">{flights.length}</span> flights
        </div>
      </section>

      {/* Flights Display */}
      <section className="flights-section">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <span>Loading flights...</span>
          </div>
        ) : flights.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No flights found</h3>
            <p>Try selecting a different date or adjusting your filters</p>
          </div>
        ) : viewMode === 'cards' ? (
          <div className="flights-grid">
            {flights.map(flight => (
              <div key={flight.id} className={`flight-card ${getStatusBadgeClass(flight.status)}`}>
                <div className="card-header">
                  <span className="flight-number">{flight.flight_number}</span>
                  <span className={`status-badge ${getStatusBadgeClass(flight.status)}`}>
                    {getStatusIcon(flight.status)} {flight.status}
                  </span>
                </div>
                
                <div className="route-display">
                  <div className="airport origin">
                    <span className="code">{flight.departure_airport}</span>
                    <span className="city">{flight.departure_city}</span>
                    <span className="time">{formatTime(flight.departure_time)}</span>
                  </div>
                  <div className="route-line">
                    <div className="line"></div>
                    <span className="plane">✈️</span>
                    <div className="line"></div>
                  </div>
                  <div className="airport destination">
                    <span className="code">{flight.arrival_airport}</span>
                    <span className="city">{flight.arrival_city}</span>
                    <span className="time">{formatTime(flight.arrival_time)}</span>
                  </div>
                </div>

                <div className="flight-details">
                  <div className="detail">
                    <span className="label">Date</span>
                    <span className="value">{formatDate(flight.departure_time)}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Gate</span>
                    <span className="value gate">{flight.departure_gate || '—'}</span>
                  </div>
                  <div className="detail occupancy">
                    <span className="label">Load</span>
                    <div className="occupancy-display">
                      <div className="occupancy-bar">
                        <div 
                          className="occupancy-fill"
                          style={{ 
                            width: `${getOccupancyPercent(flight.booked_seats, flight.total_seats)}%`,
                            backgroundColor: getOccupancyColor(flight.booked_seats, flight.total_seats)
                          }}
                        ></div>
                      </div>
                      <span className="occupancy-text">{flight.booked_seats}/{flight.total_seats}</span>
                    </div>
                  </div>
                </div>

                {flight.delay_minutes > 0 && (
                  <div className="delay-alert">
                    <span className="delay-icon">⏰</span>
                    <span>Delayed {flight.delay_minutes} min</span>
                    {flight.delay_reason && <span className="delay-reason"> • {flight.delay_reason}</span>}
                  </div>
                )}

                <div className="card-actions">
                  <button onClick={() => openStatusModal(flight)} className="btn-status">
                    ✏️ Update Status
                  </button>
                  <button onClick={() => { setSelectedFlight(flight); fetchManifest(flight.id); }} className="btn-manifest">
                    📋 Manifest
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="flights-table">
              <thead>
                <tr>
                  <th>Flight</th>
                  <th>Route</th>
                  <th>Departure</th>
                  <th>Arrival</th>
                  <th>Gate</th>
                  <th>Status</th>
                  <th>Delay</th>
                  <th>Load</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {flights.map(flight => (
                  <tr key={flight.id} className={flight.status === 'Delayed' ? 'row-delayed' : ''}>
                    <td className="td-flight">{flight.flight_number}</td>
                    <td className="td-route">
                      <span className="from">{flight.departure_airport}</span>
                      <span className="arrow">→</span>
                      <span className="to">{flight.arrival_airport}</span>
                    </td>
                    <td className="td-time">
                      <span className="time">{formatTime(flight.departure_time)}</span>
                      <span className="date">{formatDate(flight.departure_time)}</span>
                    </td>
                    <td className="td-time">
                      <span className="time">{formatTime(flight.arrival_time)}</span>
                      <span className="date">{formatDate(flight.arrival_time)}</span>
                    </td>
                    <td className="td-gate">{flight.departure_gate || '—'}</td>
                    <td>
                      <span className={`status-badge ${getStatusBadgeClass(flight.status)}`}>
                        {getStatusIcon(flight.status)} {flight.status}
                      </span>
                    </td>
                    <td className="td-delay">
                      {flight.delay_minutes > 0 ? (
                        <span className="delay-value">{flight.delay_minutes}m</span>
                      ) : '—'}
                    </td>
                    <td className="td-load">
                      <div className="mini-bar">
                        <div 
                          className="mini-fill"
                          style={{ 
                            width: `${getOccupancyPercent(flight.booked_seats, flight.total_seats)}%`,
                            backgroundColor: getOccupancyColor(flight.booked_seats, flight.total_seats)
                          }}
                        ></div>
                      </div>
                      <span className="load-text">{flight.booked_seats}/{flight.total_seats}</span>
                    </td>
                    <td className="td-actions">
                      <button onClick={() => openStatusModal(flight)} className="icon-btn" title="Update Status">✏️</button>
                      <button onClick={() => { setSelectedFlight(flight); fetchManifest(flight.id); }} className="icon-btn" title="View Manifest">📋</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Status Update Modal */}
      {showStatusModal && selectedFlight && (
        <div className="modal-overlay" onClick={() => setShowStatusModal(false)}>
          <div className="modal-content status-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Update Flight Status</h3>
              <button className="modal-close" onClick={() => setShowStatusModal(false)}>×</button>
            </div>
            
            <div className="modal-flight-badge">
              <span className="badge-flight">{selectedFlight.flight_number}</span>
              <span className="badge-route">{selectedFlight.departure_airport} → {selectedFlight.arrival_airport}</span>
              <span className="badge-time">{formatTime(selectedFlight.departure_time)} • {formatDate(selectedFlight.departure_time)}</span>
            </div>
            
            <div className="status-picker">
              <label>Select Status</label>
              <div className="status-options">
                {['Scheduled', 'Boarding', 'Delayed', 'Departed', 'Landed', 'Cancelled'].map(s => (
                  <button
                    key={s}
                    type="button"
                    className={`status-option ${getStatusBadgeClass(s)} ${statusUpdate.status === s ? 'selected' : ''}`}
                    onClick={() => setStatusUpdate({...statusUpdate, status: s})}
                  >
                    {getStatusIcon(s)} {s}
                  </button>
                ))}
              </div>
            </div>
            
            {statusUpdate.status === 'Delayed' && (
              <div className="delay-fields">
                <div className="form-row">
                  <div className="form-group">
                    <label>Delay (minutes)</label>
                    <input
                      type="number"
                      value={statusUpdate.delay_minutes}
                      onChange={(e) => setStatusUpdate({...statusUpdate, delay_minutes: parseInt(e.target.value) || 0})}
                      min="0"
                      placeholder="30"
                    />
                  </div>
                  <div className="form-group">
                    <label>Reason</label>
                    <select
                      value={statusUpdate.delay_reason}
                      onChange={(e) => setStatusUpdate({...statusUpdate, delay_reason: e.target.value})}
                    >
                      <option value="">Select reason...</option>
                      <option value="Weather conditions">🌧️ Weather conditions</option>
                      <option value="Technical issue">🔧 Technical issue</option>
                      <option value="Crew delay">👨‍✈️ Crew delay</option>
                      <option value="Air traffic control">🗼 Air traffic control</option>
                      <option value="Security reasons">🔒 Security reasons</option>
                      <option value="Late incoming aircraft">🛬 Late incoming aircraft</option>
                      <option value="Operational reasons">⚙️ Operational reasons</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
            
            <div className="form-group remarks">
              <label>Remarks (optional)</label>
              <textarea
                value={statusUpdate.remarks}
                onChange={(e) => setStatusUpdate({...statusUpdate, remarks: e.target.value})}
                placeholder="Additional information for passengers..."
                rows={3}
              />
            </div>
            
            <div className="modal-actions">
              <button onClick={() => setShowStatusModal(false)} className="btn-cancel">Cancel</button>
              <button onClick={updateFlightStatus} className="btn-update">
                ✓ Update Status
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Passenger Manifest Modal */}
      {manifest && (
        <div className="modal-overlay" onClick={() => setManifest(null)}>
          <div className="modal-content manifest-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Passenger Manifest</h3>
              <button className="modal-close" onClick={() => setManifest(null)}>×</button>
            </div>
            
            <div className="manifest-header">
              <div className="manifest-flight">
                <span className="mf-number">{manifest.flight_number}</span>
                <span className="mf-route">{manifest.route}</span>
              </div>
              <div className="manifest-stats">
                <div className="ms-item">
                  <span className="ms-value">{manifest.booked_seats}</span>
                  <span className="ms-label">Passengers</span>
                </div>
                <div className="ms-item">
                  <span className="ms-value">{manifest.total_seats - manifest.booked_seats}</span>
                  <span className="ms-label">Empty</span>
                </div>
                <div className="ms-item">
                  <span className={`ms-value status-badge ${getStatusBadgeClass(manifest.status)}`}>
                    {manifest.status}
                  </span>
                  <span className="ms-label">Status</span>
                </div>
              </div>
            </div>
            
            <div className="manifest-body">
              {manifest.passengers.length === 0 ? (
                <div className="empty-manifest">
                  <span className="em-icon">📭</span>
                  <p>No passengers booked on this flight</p>
                </div>
              ) : (
                <table className="manifest-table">
                  <thead>
                    <tr>
                      <th>Seat</th>
                      <th>Passenger</th>
                      <th>Age</th>
                      <th>Gender</th>
                      <th>Class</th>
                      <th>PNR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manifest.passengers.map((pax, idx) => (
                      <tr key={idx}>
                        <td className="td-seat">{pax.seat_number || '—'}</td>
                        <td className="td-name">{pax.passenger_name}</td>
                        <td>{pax.passenger_age || '—'}</td>
                        <td>{pax.passenger_gender || '—'}</td>
                        <td>
                          <span className={`class-badge ${pax.seat_class.toLowerCase().replace(' ', '-')}`}>
                            {pax.seat_class}
                          </span>
                        </td>
                        <td className="td-pnr">{pax.booking_pnr || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            
            <div className="modal-actions">
              <button onClick={() => setManifest(null)} className="btn-cancel">Close</button>
              <button className="btn-print" onClick={() => window.print()}>
                🖨️ Print Manifest
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AirlineDashboard;
