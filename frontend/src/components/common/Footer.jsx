import { Plane, Mail, Phone, MapPin, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        {/* Brand Section */}
        <div className="footer-brand">
          <div className="footer-logo">
            <Plane className="logo-icon" />
            <span>FlightBooker</span>
          </div>
          <p className="footer-tagline">
            Your trusted partner for seamless flight bookings. 
            Explore the skies with comfort and confidence.
          </p>
          <div className="social-links">
            <a href="#" className="social-link"><Facebook size={20} /></a>
            <a href="#" className="social-link"><Twitter size={20} /></a>
            <a href="#" className="social-link"><Instagram size={20} /></a>
            <a href="#" className="social-link"><Linkedin size={20} /></a>
          </div>
        </div>

        {/* Quick Links */}
        <div className="footer-section">
          <h4>Quick Links</h4>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/flights">Search Flights</Link></li>
            <li><Link to="/my-bookings">My Bookings</Link></li>
            <li><Link to="/about">About Us</Link></li>
          </ul>
        </div>

        {/* Support */}
        <div className="footer-section">
          <h4>Support</h4>
          <ul>
            <li><Link to="/faq">FAQ</Link></li>
            <li><Link to="/contact">Contact Us</Link></li>
            <li><Link to="/terms">Terms & Conditions</Link></li>
            <li><Link to="/privacy">Privacy Policy</Link></li>
          </ul>
        </div>

        {/* Contact Info */}
        <div className="footer-section">
          <h4>Contact Us</h4>
          <div className="contact-info">
            <div className="contact-item">
              <Mail size={16} />
              <span>support@flightbooker.com</span>
            </div>
            <div className="contact-item">
              <Phone size={16} />
              <span>+91 1800-123-4567</span>
            </div>
            <div className="contact-item">
              <MapPin size={16} />
              <span>Mumbai, India</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} FlightBooker. All rights reserved.</p>
        <p>Made with ❤️ for travelers worldwide</p>
      </div>
    </footer>
  );
};

export default Footer;
