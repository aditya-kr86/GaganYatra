import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { checkAPIHealth } from './api/config';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ProfilePage from './pages/ProfilePage';
import MyBookingsPage from './pages/MyBookingsPage';
import AboutPage from './pages/AboutPage';
import FlightsPage from './pages/FlightsPage';
import AdminDashboard from './pages/AdminDashboard';
import AirlineDashboard from './pages/AirlineDashboard';
import AirportDashboard from './pages/AirportDashboard';
import BookingPage from './pages/BookingPage';
import BookingConfirmationPage from './pages/BookingConfirmationPage';
import FAQPage from './pages/FAQPage';
import ContactPage from './pages/ContactPage';
import TermsPage from './pages/TermsPage';
import PrivacyPage from './pages/PrivacyPage';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking', 'online', 'offline'

  useEffect(() => {
    const checkBackend = async () => {
      const isHealthy = await checkAPIHealth();
      setBackendStatus(isHealthy ? 'online' : 'offline');
    };
    checkBackend();
    
    // Re-check every 30 seconds if offline
    const interval = setInterval(() => {
      if (backendStatus === 'offline') {
        checkBackend();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [backendStatus]);

  return (
    <AuthProvider>
      <Router>
        <div className="app">
          {/* Backend offline warning */}
          {backendStatus === 'offline' && (
            <div className="backend-warning">
              ⚠️ Backend server is not running. Please start the backend server on port 8000.
              <button onClick={() => setBackendStatus('checking')}>Retry</button>
            </div>
          )}
          
          <Routes>
            {/* Public routes with Navbar/Footer */}
            <Route path="/" element={
              <>
                <Navbar />
                <LandingPage />
                <Footer />
              </>
            } />
            
            {/* Auth routes (no Navbar/Footer) */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            
            {/* Public pages with Navbar/Footer included in component */}
            <Route path="/about" element={<AboutPage />} />
            <Route path="/flights" element={<FlightsPage />} />
            <Route path="/faq" element={<FAQPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            
            {/* Protected routes (Navbar/Footer included in page) */}
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/my-bookings" element={<MyBookingsPage />} />
            
            {/* Booking routes */}
            <Route path="/booking/new" element={<BookingPage />} />
            <Route path="/booking/confirmation/:pnr" element={<BookingConfirmationPage />} />
            
            {/* Admin routes (no Navbar/Footer - has its own layout) */}
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            
            {/* Staff Dashboards */}
            <Route path="/airline/dashboard" element={<AirlineDashboard />} />
            <Route path="/airport/dashboard" element={<AirportDashboard />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
