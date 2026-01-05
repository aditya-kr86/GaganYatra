import { Link } from 'react-router-dom';
import { Plane, Shield, Clock, Users, Award, Globe, HeadphonesIcon, Heart } from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './AboutPage.css';

const AboutPage = () => {
  const stats = [
    { number: '10M+', label: 'Happy Travelers' },
    { number: '500+', label: 'Destinations' },
    { number: '50+', label: 'Partner Airlines' },
    { number: '24/7', label: 'Customer Support' },
  ];

  const values = [
    {
      icon: <Shield size={32} />,
      title: 'Trust & Security',
      description: 'Your bookings are protected with industry-leading security measures and transparent pricing.'
    },
    {
      icon: <Clock size={32} />,
      title: 'Reliability',
      description: 'Count on us for accurate flight information and timely updates on your travel plans.'
    },
    {
      icon: <Users size={32} />,
      title: 'Customer First',
      description: 'Every decision we make is centered around providing the best experience for our travelers.'
    },
    {
      icon: <Heart size={32} />,
      title: 'Passion for Travel',
      description: 'We believe travel transforms lives, and we\'re passionate about making it accessible to all.'
    },
  ];

  const team = [
    { name: 'Aditya Kumar', role: 'Founder & CEO', image: '👨‍💼' },
    { name: 'Priya Sharma', role: 'CTO', image: '👩‍💻' },
    { name: 'Rahul Verma', role: 'Head of Operations', image: '👨‍✈️' },
    { name: 'Sneha Patel', role: 'Customer Experience', image: '👩‍💼' },
  ];

  return (
    <>
      <Navbar />
      <div className="about-page">
        {/* Hero Section */}
        <section className="about-hero">
          <div className="about-hero-content">
            <div className="hero-badge">
              <Plane size={20} />
              <span>About FlightBooker</span>
            </div>
            <h1>Making Air Travel <span className="gradient-text">Simple & Affordable</span></h1>
            <p>
              FlightBooker is your trusted flight booking platform, 
              connecting millions of travelers to their dream destinations with the best prices 
              and seamless booking experience.
            </p>
          </div>
        </section>

        {/* Stats Section */}
        <section className="about-stats">
          <div className="stats-container">
            {stats.map((stat, index) => (
              <div key={index} className="stat-card">
                <span className="stat-number">{stat.number}</span>
                <span className="stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Story Section */}
        <section className="about-story">
          <div className="story-container">
            <div className="story-content">
              <h2>Our Story</h2>
              <p>
                Founded in 2024, FlightBooker was born from a simple idea: making air travel 
                booking as effortless as possible for every traveler. What started as 
                a small startup has grown into a comprehensive travel platform trusted by 
                millions.
              </p>
              <p>
                Our name, derived from Sanskrit, means "Sky Journey" – reflecting our 
                commitment to making every journey through the skies a memorable experience. 
                We combine cutting-edge technology with deep understanding of Indian travelers' 
                needs to deliver unmatched service.
              </p>
              <p>
                Today, we partner with over 50 airlines and serve destinations across India 
                and the world, all while maintaining our core values of transparency, 
                reliability, and customer-first approach.
              </p>
            </div>
            <div className="story-image">
              <div className="image-placeholder">
                <Globe size={120} />
                <span>Connecting India to the World</span>
              </div>
            </div>
          </div>
        </section>

        {/* Values Section */}
        <section className="about-values">
          <div className="values-header">
            <h2>Our Values</h2>
            <p>The principles that guide everything we do</p>
          </div>
          <div className="values-grid">
            {values.map((value, index) => (
              <div key={index} className="value-card">
                <div className="value-icon">{value.icon}</div>
                <h3>{value.title}</h3>
                <p>{value.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Team Section */}
        <section className="about-team">
          <div className="team-header">
            <h2>Meet Our Team</h2>
            <p>The passionate people behind FlightBooker</p>
          </div>
          <div className="team-grid">
            {team.map((member, index) => (
              <div key={index} className="team-card">
                <div className="team-avatar">{member.image}</div>
                <h3>{member.name}</h3>
                <p>{member.role}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features Section */}
        <section className="about-features">
          <div className="features-container">
            <div className="feature-item">
              <Award size={40} />
              <h3>Award Winning Service</h3>
              <p>Recognized for excellence in customer service and innovation</p>
            </div>
            <div className="feature-item">
              <HeadphonesIcon size={40} />
              <h3>24/7 Support</h3>
              <p>Our team is always ready to assist you, day or night</p>
            </div>
            <div className="feature-item">
              <Shield size={40} />
              <h3>Secure Payments</h3>
              <p>Multiple payment options with bank-grade security</p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="about-cta">
          <div className="cta-content">
            <h2>Ready to Start Your Journey?</h2>
            <p>Book your next flight with FlightBooker and experience the difference</p>
            <Link to="/" className="cta-button">
              <Plane size={20} />
              Search Flights
            </Link>
          </div>
        </section>
      </div>
      <Footer />
    </>
  );
};

export default AboutPage;
