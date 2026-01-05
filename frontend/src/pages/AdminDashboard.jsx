import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/config';
import { 
  LayoutDashboard, Plane, Building2, Users, Ticket, Settings, LogOut,
  Plus, Search, Edit, Trash2, ChevronRight, TrendingUp, DollarSign,
  Calendar, AlertCircle, Loader2, X, Check
} from 'lucide-react';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const { user, token, logout, isAdmin, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    totalFlights: 0,
    totalAirports: 0,
    totalAirlines: 0,
    totalUsers: 0,
    totalBookings: 0,
  });
  const [airports, setAirports] = useState([]);
  const [airlines, setAirlines] = useState([]);
  const [users, setUsers] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Modal states
  const [showAirportModal, setShowAirportModal] = useState(false);
  const [showAirlineModal, setShowAirlineModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  useEffect(() => {
    if (!authLoading && (!isAuthenticated() || !isAdmin())) {
      navigate('/login');
    }
  }, [authLoading, isAuthenticated, isAdmin, navigate]);

  useEffect(() => {
    if (token && isAdmin()) {
      fetchData();
    }
  }, [token]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [airportsRes, airlinesRes, usersRes, flightsRes, bookingsRes] = await Promise.all([
        api.get('/airports/').catch(() => ({ data: [] })),
        api.get('/airlines/').catch(() => ({ data: [] })),
        api.get('/users/').catch(() => ({ data: [] })),
        api.get('/flights/').catch(() => ({ data: [] })),
        api.get('/bookings/').catch(() => ({ data: [] })),
      ]);

      setAirports(airportsRes.data || []);
      setAirlines(airlinesRes.data || []);
      setUsers(usersRes.data || []);
      setBookings(bookingsRes.data || []);
      
      setStats({
        totalFlights: flightsRes.data?.length || 0,
        totalAirports: airportsRes.data?.length || 0,
        totalAirlines: airlinesRes.data?.length || 0,
        totalUsers: usersRes.data?.length || 0,
        totalBookings: bookingsRes.data?.length || 0,
      });
    } catch (err) {
      console.error('Failed to load admin data:', err);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  // Airport CRUD
  const handleSaveAirport = async (formData) => {
    try {
      if (editingItem) {
        await api.put(`/airports/${editingItem.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/airports', formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowAirportModal(false);
      setEditingItem(null);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save airport');
    }
  };

  const handleDeleteAirport = async (id) => {
    if (!confirm('Are you sure you want to delete this airport?')) return;
    try {
      await api.delete(`/airports/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete airport');
    }
  };

  // Airline CRUD
  const handleSaveAirline = async (formData) => {
    try {
      if (editingItem) {
        await api.put(`/airlines/${editingItem.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/airlines', formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowAirlineModal(false);
      setEditingItem(null);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save airline');
    }
  };

  const handleDeleteAirline = async (id) => {
    if (!confirm('Are you sure you want to delete this airline?')) return;
    try {
      await api.delete(`/airlines/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete airline');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="admin-loading">
        <Loader2 className="spinner" size={48} />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="sidebar-header">
          <Link to="/" className="sidebar-logo">
            <Plane size={28} />
            <span>FlightBooker</span>
          </Link>
          <span className="admin-badge">Admin</span>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <LayoutDashboard size={20} />
            Overview
          </button>
          <button 
            className={`nav-item ${activeTab === 'airports' ? 'active' : ''}`}
            onClick={() => setActiveTab('airports')}
          >
            <Building2 size={20} />
            Airports
          </button>
          <button 
            className={`nav-item ${activeTab === 'airlines' ? 'active' : ''}`}
            onClick={() => setActiveTab('airlines')}
          >
            <Plane size={20} />
            Airlines
          </button>
          <button 
            className={`nav-item ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <Users size={20} />
            Users
          </button>
          <button 
            className={`nav-item ${activeTab === 'bookings' ? 'active' : ''}`}
            onClick={() => setActiveTab('bookings')}
          >
            <Ticket size={20} />
            Bookings
          </button>
        </nav>

        <div className="sidebar-footer">
          <Link to="/" className="nav-item">
            <ChevronRight size={20} />
            Back to Site
          </Link>
          <button className="nav-item logout" onClick={handleLogout}>
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="admin-main">
        <header className="admin-header">
          <div>
            <h1>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h1>
            <p>Welcome back, {user?.first_name}</p>
          </div>
          <div className="header-actions">
            {activeTab === 'airports' && (
              <button className="add-btn" onClick={() => { setEditingItem(null); setShowAirportModal(true); }}>
                <Plus size={18} />
                Add Airport
              </button>
            )}
            {activeTab === 'airlines' && (
              <button className="add-btn" onClick={() => { setEditingItem(null); setShowAirlineModal(true); }}>
                <Plus size={18} />
                Add Airline
              </button>
            )}
          </div>
        </header>

        <div className="admin-content">
          {error && (
            <div className="error-banner">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="overview-section">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon flights">
                    <Plane size={24} />
                  </div>
                  <div className="stat-info">
                    <span className="stat-value">{stats.totalFlights}</span>
                    <span className="stat-label">Total Flights</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon airports">
                    <Building2 size={24} />
                  </div>
                  <div className="stat-info">
                    <span className="stat-value">{stats.totalAirports}</span>
                    <span className="stat-label">Airports</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon airlines">
                    <Plane size={24} />
                  </div>
                  <div className="stat-info">
                    <span className="stat-value">{stats.totalAirlines}</span>
                    <span className="stat-label">Airlines</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon users">
                    <Users size={24} />
                  </div>
                  <div className="stat-info">
                    <span className="stat-value">{stats.totalUsers}</span>
                    <span className="stat-label">Users</span>
                  </div>
                </div>
              </div>

              <div className="quick-actions">
                <h3>Quick Actions</h3>
                <div className="actions-grid">
                  <button onClick={() => { setActiveTab('airports'); setShowAirportModal(true); }}>
                    <Plus size={20} />
                    Add New Airport
                  </button>
                  <button onClick={() => { setActiveTab('airlines'); setShowAirlineModal(true); }}>
                    <Plus size={20} />
                    Add New Airline
                  </button>
                  <button onClick={() => setActiveTab('users')}>
                    <Users size={20} />
                    Manage Users
                  </button>
                  <button onClick={() => setActiveTab('bookings')}>
                    <Ticket size={20} />
                    View Bookings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Airports Tab */}
          {activeTab === 'airports' && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>City</th>
                    <th>Country</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {airports.map(airport => (
                    <tr key={airport.id}>
                      <td><span className="code-badge">{airport.code}</span></td>
                      <td>{airport.name}</td>
                      <td>{airport.city}</td>
                      <td>{airport.country}</td>
                      <td>
                        <div className="table-actions">
                          <button className="edit-btn" onClick={() => { setEditingItem(airport); setShowAirportModal(true); }}>
                            <Edit size={16} />
                          </button>
                          <button className="delete-btn" onClick={() => handleDeleteAirport(airport.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {airports.length === 0 && (
                <div className="empty-state">
                  <Building2 size={48} />
                  <p>No airports found. Add your first airport!</p>
                </div>
              )}
            </div>
          )}

          {/* Airlines Tab */}
          {activeTab === 'airlines' && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {airlines.map(airline => (
                    <tr key={airline.id}>
                      <td><span className="code-badge">{airline.code}</span></td>
                      <td>{airline.name}</td>
                      <td>
                        <div className="table-actions">
                          <button className="edit-btn" onClick={() => { setEditingItem(airline); setShowAirlineModal(true); }}>
                            <Edit size={16} />
                          </button>
                          <button className="delete-btn" onClick={() => handleDeleteAirline(airline.id)}>
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {airlines.length === 0 && (
                <div className="empty-state">
                  <Plane size={48} />
                  <p>No airlines found. Add your first airline!</p>
                </div>
              )}
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.first_name} {u.last_name}</td>
                      <td>{u.email}</td>
                      <td><span className={`role-badge ${u.role}`}>{u.role}</span></td>
                      <td>
                        <span className={`status-badge ${u.is_active ? 'active' : 'inactive'}`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <div className="empty-state">
                  <Users size={48} />
                  <p>No users found.</p>
                </div>
              )}
            </div>
          )}

          {/* Bookings Tab */}
          {activeTab === 'bookings' && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>PNR</th>
                    <th>Reference</th>
                    <th>Status</th>
                    <th>Total Fare</th>
                    <th>Passengers</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map(booking => (
                    <tr key={booking.booking_reference}>
                      <td><strong>{booking.pnr || 'Pending'}</strong></td>
                      <td>{booking.booking_reference}</td>
                      <td>
                        <span className={`status-badge ${booking.status?.toLowerCase().replace(' ', '-')}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td>₹{booking.total_fare?.toLocaleString() || 0}</td>
                      <td>{booking.tickets?.length || 0}</td>
                      <td>{new Date(booking.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {bookings.length === 0 && (
                <div className="empty-state">
                  <Ticket size={48} />
                  <p>No bookings found.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Airport Modal */}
      {showAirportModal && (
        <AirportModal
          airport={editingItem}
          onSave={handleSaveAirport}
          onClose={() => { setShowAirportModal(false); setEditingItem(null); }}
        />
      )}

      {/* Airline Modal */}
      {showAirlineModal && (
        <AirlineModal
          airline={editingItem}
          onSave={handleSaveAirline}
          onClose={() => { setShowAirlineModal(false); setEditingItem(null); }}
        />
      )}
    </div>
  );
};

// Airport Modal Component
const AirportModal = ({ airport, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    code: airport?.code || '',
    name: airport?.name || '',
    city: airport?.city || '',
    country: airport?.country || 'India',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{airport ? 'Edit Airport' : 'Add New Airport'}</h2>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Airport Code (IATA)</label>
            <input
              type="text"
              value={formData.code}
              onChange={e => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              maxLength={3}
              required
              placeholder="e.g., DEL"
            />
          </div>
          <div className="form-group">
            <label>Airport Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="e.g., Indira Gandhi International Airport"
            />
          </div>
          <div className="form-group">
            <label>City</label>
            <input
              type="text"
              value={formData.city}
              onChange={e => setFormData({ ...formData, city: e.target.value })}
              required
              placeholder="e.g., Delhi"
            />
          </div>
          <div className="form-group">
            <label>Country</label>
            <input
              type="text"
              value={formData.country}
              onChange={e => setFormData({ ...formData, country: e.target.value })}
              required
              placeholder="e.g., India"
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="save-btn">
              <Check size={18} />
              {airport ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Airline Modal Component
const AirlineModal = ({ airline, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    code: airline?.code || '',
    name: airline?.name || '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{airline ? 'Edit Airline' : 'Add New Airline'}</h2>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Airline Code (IATA)</label>
            <input
              type="text"
              value={formData.code}
              onChange={e => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              maxLength={2}
              required
              placeholder="e.g., 6E"
            />
          </div>
          <div className="form-group">
            <label>Airline Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="e.g., IndiGo"
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="save-btn">
              <Check size={18} />
              {airline ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminDashboard;
