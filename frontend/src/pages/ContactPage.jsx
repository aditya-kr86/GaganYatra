import { useState } from 'react';
import { 
  Mail, Phone, MapPin, Clock, Send, 
  MessageCircle, Headphones, CheckCircle, Loader2 
} from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './StaticPages.css';

const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setSubmitting(false);
    setSubmitted(true);
    setFormData({ name: '', email: '', phone: '', subject: '', message: '' });
  };

  const contactInfo = [
    {
      icon: <Phone />,
      title: 'Phone Support',
      primary: '1800-XXX-XXXX',
      secondary: 'Toll-free, 24/7 available',
    },
    {
      icon: <Mail />,
      title: 'Email Us',
      primary: 'support@flightbooker.com',
      secondary: 'Response within 2 hours',
    },
    {
      icon: <MapPin />,
      title: 'Head Office',
      primary: 'Tech Park, Sector 126',
      secondary: 'Noida, UP 201303, India',
    },
    {
      icon: <Clock />,
      title: 'Working Hours',
      primary: '24/7 Support Available',
      secondary: 'Office: Mon-Sat, 9AM-6PM',
    },
  ];

  const quickHelp = [
    { icon: '✈️', title: 'Flight Status', desc: 'Track your flight in real-time' },
    { icon: '🎫', title: 'Manage Booking', desc: 'View, modify or cancel bookings' },
    { icon: '💰', title: 'Refund Status', desc: 'Track your refund request' },
    { icon: '📱', title: 'Web Check-in', desc: 'Check in online before travel' },
  ];

  return (
    <>
      <Navbar />
      <div className="static-page contact-page">
        <div className="static-hero">
          <div className="hero-content">
            <Headphones size={48} />
            <h1>Contact Us</h1>
            <p>We're here to help! Reach out to us anytime</p>
          </div>
        </div>

        <div className="static-container">
          {/* Contact Cards */}
          <div className="contact-cards">
            {contactInfo.map((info, index) => (
              <div key={index} className="contact-card">
                <div className="contact-icon">{info.icon}</div>
                <h3>{info.title}</h3>
                <p className="primary">{info.primary}</p>
                <p className="secondary">{info.secondary}</p>
              </div>
            ))}
          </div>

          {/* Quick Help */}
          <div className="quick-help-section">
            <h2>Quick Help</h2>
            <div className="quick-help-grid">
              {quickHelp.map((item, index) => (
                <div key={index} className="quick-help-card">
                  <span className="qh-icon">{item.icon}</span>
                  <div>
                    <h4>{item.title}</h4>
                    <p>{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contact Form */}
          <div className="contact-form-section">
            <div className="form-header">
              <MessageCircle size={32} />
              <h2>Send us a Message</h2>
              <p>Fill out the form below and we'll get back to you shortly</p>
            </div>

            {submitted ? (
              <div className="success-message">
                <CheckCircle size={64} />
                <h3>Message Sent Successfully!</h3>
                <p>Thank you for contacting us. Our team will respond within 2 hours.</p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setSubmitted(false)}
                >
                  Send Another Message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="contact-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Full Name *</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Enter your name"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Email Address *</label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Phone Number</label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+91 XXXXX XXXXX"
                    />
                  </div>
                  <div className="form-group">
                    <label>Subject *</label>
                    <select
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Select a topic</option>
                      <option value="booking">Booking Issue</option>
                      <option value="refund">Refund Request</option>
                      <option value="cancellation">Cancellation</option>
                      <option value="payment">Payment Problem</option>
                      <option value="feedback">Feedback</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Message *</label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    placeholder="Describe your query in detail..."
                    rows="5"
                    required
                  />
                </div>

                <button 
                  type="submit" 
                  className="btn btn-primary submit-btn"
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="spinner" size={18} />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Send Message
                    </>
                  )}
                </button>
              </form>
            )}
          </div>

          {/* Map Section */}
          <div className="map-section">
            <h2>Find Us</h2>
            <div className="map-placeholder">
              <MapPin size={48} />
              <p>Tech Park, Sector 126, Noida, UP 201303</p>
              <span>Interactive map coming soon</span>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default ContactPage;
