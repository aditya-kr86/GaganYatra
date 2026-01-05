import { 
  Zap, 
  Shield, 
  Clock, 
  CreditCard, 
  Headphones, 
  TrendingDown 
} from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <Zap />,
      title: 'Dynamic Pricing',
      description: 'Get the best fares with our real-time dynamic pricing engine that adjusts based on demand and availability.',
    },
    {
      icon: <Shield />,
      title: 'Secure Bookings',
      description: 'Your transactions are protected with enterprise-grade security and encrypted payment processing.',
    },
    {
      icon: <Clock />,
      title: 'Instant Confirmation',
      description: 'Receive immediate booking confirmation with your e-ticket and PNR delivered to your inbox.',
    },
    {
      icon: <CreditCard />,
      title: 'Flexible Payments',
      description: 'Multiple payment options including cards, UPI, net banking, and wallet payments.',
    },
    {
      icon: <Headphones />,
      title: '24/7 Support',
      description: 'Round-the-clock customer support to assist you with bookings, changes, and queries.',
    },
    {
      icon: <TrendingDown />,
      title: 'Price Alerts',
      description: 'Set price alerts and get notified when fares drop for your preferred routes.',
    },
  ];

  return (
    <section className="features-section">
      <div className="features-container">
        <div className="section-header">
          <h2>Why Choose FlightBooker?</h2>
          <p>Experience hassle-free flight booking with features designed for modern travelers</p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
