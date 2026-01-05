import { Plane, Shield, Clock, CreditCard } from 'lucide-react';
import FlightSearchForm from './FlightSearchForm';

const Hero = () => {
  return (
    <section className="hero">
      <div className="hero-background">
        <div className="hero-overlay"></div>
      </div>
      
      <div className="hero-content">
        <div className="hero-text">
          <h1 className="hero-title">
            Explore the <span className="highlight">Skies</span> with FlightBooker
          </h1>
          <p className="hero-subtitle">
            Book your dream flights at the best prices. Discover seamless travel 
            experiences with our dynamic pricing and real-time availability.
          </p>
          
          {/* Trust Badges */}
          <div className="trust-badges">
            <div className="badge">
              <Shield size={20} />
              <span>Secure Booking</span>
            </div>
            <div className="badge">
              <Clock size={20} />
              <span>24/7 Support</span>
            </div>
            <div className="badge">
              <CreditCard size={20} />
              <span>Easy Payments</span>
            </div>
          </div>
        </div>

        {/* Flight Search Form */}
        <div className="hero-search">
          <FlightSearchForm />
        </div>
      </div>

      {/* Floating Planes Animation */}
      <div className="floating-planes">
        <Plane className="floating-plane plane-1" />
        <Plane className="floating-plane plane-2" />
        <Plane className="floating-plane plane-3" />
      </div>
    </section>
  );
};

export default Hero;
