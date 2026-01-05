import { useState } from 'react';
import { ChevronDown, ChevronUp, Search, HelpCircle } from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './StaticPages.css';

const FAQPage = () => {
  const [openIndex, setOpenIndex] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const faqCategories = [
    {
      category: 'Booking & Reservations',
      icon: '✈️',
      faqs: [
        {
          question: 'How do I book a flight on FlightBooker?',
          answer: 'Booking a flight is simple! Enter your departure and arrival cities, select your travel dates, and choose the number of passengers. Browse available flights, select your preferred option, enter passenger details, and complete the payment. You\'ll receive an instant confirmation with your PNR.'
        },
        {
          question: 'Can I book a flight for someone else?',
          answer: 'Yes, you can book flights for others. Simply enter the passenger details of the person who will be traveling. Make sure all information matches their government-issued ID exactly.'
        },
        {
          question: 'How far in advance can I book a flight?',
          answer: 'You can book flights up to 365 days in advance, subject to availability. We recommend booking at least 2-3 weeks ahead for domestic flights and 4-6 weeks for the best fares.'
        },
        {
          question: 'What is a PNR and where can I find it?',
          answer: 'PNR (Passenger Name Record) is a unique 6-character alphanumeric code that identifies your booking. You\'ll find it in your confirmation email, on your e-ticket, and in the "My Bookings" section of your account.'
        }
      ]
    },
    {
      category: 'Payments & Pricing',
      icon: '💳',
      faqs: [
        {
          question: 'What payment methods are accepted?',
          answer: 'We accept Credit/Debit Cards (Visa, Mastercard, RuPay), UPI payments, Net Banking from all major banks, and popular digital wallets. All transactions are secured with industry-standard encryption.'
        },
        {
          question: 'How does dynamic pricing work?',
          answer: 'Our dynamic pricing engine adjusts fares based on real-time factors including demand, seat availability, time until departure, and seasonal trends. Booking early typically offers better prices, and prices may increase as seats fill up.'
        },
        {
          question: 'Are there any hidden charges?',
          answer: 'No hidden charges! The price shown includes all taxes and fees. Any additional services like extra baggage or seat selection will be clearly displayed before payment.'
        },
        {
          question: 'Can I get a refund if I cancel my booking?',
          answer: 'Refund policies vary by airline and fare type. Economy Flex and higher tiers typically offer partial to full refunds. Check the fare rules before booking or visit "My Bookings" for specific cancellation terms.'
        }
      ]
    },
    {
      category: 'Changes & Cancellations',
      icon: '🔄',
      faqs: [
        {
          question: 'How do I cancel my booking?',
          answer: 'Log in to your account, go to "My Bookings", find your reservation, and click "Cancel". You\'ll see the applicable cancellation fee and refund amount before confirming. Cancellations are processed within 24 hours.'
        },
        {
          question: 'Can I change my flight date or time?',
          answer: 'Date and time changes depend on the airline\'s policy and your fare type. Contact our support team or visit "My Bookings" to check modification options. Additional fare differences may apply.'
        },
        {
          question: 'What happens if my flight is cancelled by the airline?',
          answer: 'If the airline cancels your flight, you\'ll be notified immediately via email and SMS. You\'ll be offered either a full refund or rebooking on an alternative flight at no extra cost.'
        },
        {
          question: 'Is there a free cancellation window?',
          answer: 'Yes! You can cancel your booking free of charge within 24 hours of making the reservation, provided the departure is at least 7 days away.'
        }
      ]
    },
    {
      category: 'Check-in & Boarding',
      icon: '🎫',
      faqs: [
        {
          question: 'How do I check in for my flight?',
          answer: 'Web check-in opens 48 hours before departure. You can check in through the airline\'s website or at the airport counter. Arrive at least 2 hours before domestic flights and 3 hours before international flights.'
        },
        {
          question: 'What documents do I need at the airport?',
          answer: 'For domestic flights: A valid government-issued photo ID (Aadhaar, Passport, Driving License, Voter ID, or PAN Card) and your e-ticket/PNR. For international flights: Valid passport, visa (if required), and e-ticket.'
        },
        {
          question: 'Can I select my seat in advance?',
          answer: 'Seat selection is available during booking or later through "My Bookings". Some seats may have additional charges. Alternatively, seats are assigned during check-in.'
        },
        {
          question: 'What is the baggage allowance?',
          answer: 'Baggage allowance varies by airline and fare class. Typically, Economy allows 15-20kg check-in + 7kg cabin baggage, while Business class offers 30-35kg + 7kg cabin. Check your booking details for specific limits.'
        }
      ]
    },
    {
      category: 'Account & Support',
      icon: '👤',
      faqs: [
        {
          question: 'How do I create an account?',
          answer: 'Click "Sign Up" on the homepage, enter your email, create a password, and fill in your profile details. You can also sign up using your Google account for faster registration.'
        },
        {
          question: 'I forgot my password. How do I reset it?',
          answer: 'Click "Forgot Password" on the login page, enter your registered email, and we\'ll send you a password reset link. The link expires in 24 hours for security.'
        },
        {
          question: 'How can I contact customer support?',
          answer: 'Our 24/7 support is available via: Email at support@flightbooker.com, Phone at 1800-XXX-XXXX (toll-free), or Live Chat on our website and app. Response time is typically under 2 hours.'
        },
        {
          question: 'How do I view my past bookings?',
          answer: 'Log in to your account and click "My Bookings" in the navigation menu. You\'ll see all your upcoming and past reservations with options to download tickets and invoices.'
        }
      ]
    }
  ];

  const filteredFAQs = faqCategories.map(category => ({
    ...category,
    faqs: category.faqs.filter(faq =>
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.faqs.length > 0);

  const toggleFAQ = (categoryIndex, faqIndex) => {
    const key = `${categoryIndex}-${faqIndex}`;
    setOpenIndex(openIndex === key ? null : key);
  };

  return (
    <>
      <Navbar />
      <div className="static-page faq-page">
        <div className="static-hero">
          <div className="hero-content">
            <HelpCircle size={48} />
            <h1>Frequently Asked Questions</h1>
            <p>Find answers to common questions about booking, payments, and travel</p>
          </div>
        </div>

        <div className="static-container">
          <div className="faq-search">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search for answers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="faq-categories">
            {filteredFAQs.map((category, catIndex) => (
              <div key={catIndex} className="faq-category">
                <div className="category-header">
                  <span className="category-icon">{category.icon}</span>
                  <h2>{category.category}</h2>
                </div>

                <div className="faq-list">
                  {category.faqs.map((faq, faqIndex) => {
                    const key = `${catIndex}-${faqIndex}`;
                    const isOpen = openIndex === key;

                    return (
                      <div key={faqIndex} className={`faq-item ${isOpen ? 'open' : ''}`}>
                        <button
                          className="faq-question"
                          onClick={() => toggleFAQ(catIndex, faqIndex)}
                        >
                          <span>{faq.question}</span>
                          {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                        {isOpen && (
                          <div className="faq-answer">
                            <p>{faq.answer}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {filteredFAQs.length === 0 && (
            <div className="no-results">
              <HelpCircle size={48} />
              <h3>No results found</h3>
              <p>Try different keywords or browse our categories above</p>
            </div>
          )}

          <div className="still-need-help">
            <h3>Still need help?</h3>
            <p>Our support team is available 24/7 to assist you</p>
            <a href="/contact" className="btn btn-primary">Contact Support</a>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default FAQPage;
