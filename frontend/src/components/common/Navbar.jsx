import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plane, Menu, X, User, LogOut, Settings, Ticket, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
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
    </nav>
  );
};

export default Navbar;
