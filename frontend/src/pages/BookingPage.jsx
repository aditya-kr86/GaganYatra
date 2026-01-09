import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import SeatSelector from '../components/common/SeatSelector';
import { flightAPI } from '../api/flights';
import api from '../api/config';
import { 
  Plane, Users, CreditCard, CheckCircle, ArrowLeft, ArrowRight,
  User, Calendar, MapPin, Clock, AlertCircle, Loader2,
  IndianRupee, Shield, ChevronRight, Plus, Trash2, Armchair
} from 'lucide-react';
import './BookingPage.css';

const STEPS = [
  { id: 1, name: 'Passenger Details', icon: Users },
  { id: 2, name: 'Select Seats', icon: Armchair },
  { id: 3, name: 'Review Booking', icon: CheckCircle },
  { id: 4, name: 'Payment', icon: CreditCard },
];

const BookingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();

  // URL params
  const flightId = searchParams.get('flight');
  const passengersCount = parseInt(searchParams.get('passengers') || '1');
  const seatTier = searchParams.get('tier') || 'ECONOMY';
  const urlPrice = parseFloat(searchParams.get('price') || '0');

  // State
  const [currentStep, setCurrentStep] = useState(1);
  const [flight, setFlight] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Locked price from URL (set once and never changed)
  const [lockedPrice, setLockedPrice] = useState(urlPrice);

  // Passenger form state - start with initial count from URL
  const [passengers, setPassengers] = useState(
    Array.from({ length: passengersCount }, () => ({
      passenger_name: '',
      age: '',
      gender: '',
    }))
  );

  // Seat selection state
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [seatSurcharge, setSeatSurcharge] = useState(0);

  // Add new passenger
  const addPassenger = () => {
    if (passengers.length >= 9) {
      setError('Maximum 9 passengers allowed per booking');
      return;
    }
    setPassengers(prev => [...prev, { passenger_name: '', age: '', gender: '' }]);
    // Clear seat selection when passenger count changes
    setSelectedSeats([]);
    setSeatSurcharge(0);
    setError('');
  };

  // Remove passenger (keep at least 1)
  const removePassenger = (index) => {
    if (passengers.length <= 1) return;
    setPassengers(prev => prev.filter((_, i) => i !== index));
    // Clear seat selection when passenger count changes
    setSelectedSeats([]);
    setSeatSurcharge(0);
    setError('');
  };

  // Handle seat selection from SeatSelector component
  const handleSeatSelect = (seats) => {
    setSelectedSeats(seats);
    const totalSurcharge = seats.reduce((sum, seat) => sum + (seat.surcharge || 0), 0);
    setSeatSurcharge(totalSurcharge);
  };

  // Payment form state
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [cardDetails, setCardDetails] = useState({
    number: '',
    name: '',
    expiry: '',
    cvv: '',
  });
  const [upiId, setUpiId] = useState('');
  const [selectedBank, setSelectedBank] = useState('');

  // Check authentication on mount
  useEffect(() => {
    if (!authLoading && !user) {
      // Redirect to login with return URL
      navigate('/login', { 
        state: { from: location },
        replace: true 
      });
    }
  }, [user, authLoading, navigate, location]);

  // Fetch flight details
  useEffect(() => {
    const fetchFlight = async () => {
      if (!flightId) {
        setError('No flight selected');
        setLoading(false);
        return;
      }

      try {
        const data = await flightAPI.getFlightById(flightId);
        setFlight(data);
        
        // If no URL price was provided, compute it from the flight data
        if (urlPrice === 0) {
          const basePrice = data.dynamic_price || data.current_price || data.base_price || 0;
          const multipliers = {
            'ECONOMY': 1.0,
            'ECONOMY_FLEX': 1.2,
            'BUSINESS': 1.8,
            'FIRST': 2.5,
          };
          const computed = basePrice * (multipliers[seatTier] || 1.0);
          setLockedPrice(computed);
        }
      } catch (err) {
        setError('Failed to load flight details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchFlight();
    }
  }, [flightId, user, urlPrice, seatTier]);

  // Use locked price for all calculations - use actual passengers.length for dynamic count
  const tierPrice = lockedPrice;
  const baseTotalPrice = tierPrice * passengers.length;
  const totalPrice = baseTotalPrice + seatSurcharge; // Include seat surcharges

  // Handle passenger input change
  const handlePassengerChange = (index, field, value) => {
    setPassengers(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  // Pre-fill first passenger with logged-in user
  useEffect(() => {
    if (user && passengers[0]?.passenger_name === '') {
      setPassengers(prev => {
        const updated = [...prev];
        updated[0] = {
          ...updated[0],
          passenger_name: `${user.first_name} ${user.last_name}`,
        };
        return updated;
      });
    }
  }, [user]);

  // Validate current step
  const validateStep = () => {
    if (currentStep === 1) {
      // Validate passenger details
      for (let i = 0; i < passengers.length; i++) {
        const p = passengers[i];
        if (!p.passenger_name?.trim()) {
          setError(`Please enter name for Passenger ${i + 1}`);
          return false;
        }
        if (!p.age || p.age < 1 || p.age > 120) {
          setError(`Please enter valid age for Passenger ${i + 1}`);
          return false;
        }
        if (!p.gender) {
          setError(`Please select gender for Passenger ${i + 1}`);
          return false;
        }
      }
    }
    
    if (currentStep === 2) {
      // Validate seat selection
      if (selectedSeats.length !== passengers.length) {
        setError(`Please select ${passengers.length} seat(s) for all passengers. Currently selected: ${selectedSeats.length}`);
        return false;
      }
    }
    
    if (currentStep === 4) {
      // Validate payment
      if (paymentMethod === 'card') {
        if (!cardDetails.number || cardDetails.number.replace(/\s/g, '').length !== 16) {
          setError('Please enter valid 16-digit card number');
          return false;
        }
        if (!cardDetails.name?.trim()) {
          setError('Please enter cardholder name');
          return false;
        }
        if (!cardDetails.expiry || !/^\d{2}\/\d{2}$/.test(cardDetails.expiry)) {
          setError('Please enter valid expiry date (MM/YY)');
          return false;
        }
        if (!cardDetails.cvv || cardDetails.cvv.length < 3) {
          setError('Please enter valid CVV');
          return false;
        }
      } else if (paymentMethod === 'upi') {
        if (!upiId || !upiId.includes('@')) {
          setError('Please enter valid UPI ID');
          return false;
        }
      } else if (paymentMethod === 'netbanking') {
        if (!selectedBank) {
          setError('Please select a bank for Net Banking');
          return false;
        }
      }
    }
    
    setError('');
    return true;
  };

  // Handle next step
  const handleNext = () => {
    if (validateStep()) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  // Handle previous step
  const handleBack = () => {
    setError('');
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  // Handle booking submission
  const handleSubmit = async () => {
    if (!validateStep()) return;
    
    setSubmitting(true);
    setError('');

    try {
      // Step 1: Create booking with selected seats
      const departureDate = new Date(flight.departure_time).toISOString().split('T')[0];
      
      // Include selected seat IDs in the booking payload
      const selectedSeatIds = selectedSeats.map(s => s.id);
      
      const bookingPayload = {
        user_id: user.id,
        flight_number: flight.flight_number,
        departure_date: departureDate,
        passengers: passengers.map((p, idx) => ({
          passenger_name: p.passenger_name,
          age: parseInt(p.age),
          gender: p.gender,
          seat_id: selectedSeatIds[idx] || null,
        })),
        seat_class: seatTier,
        selected_seat_ids: selectedSeatIds,
      };

      const bookingResponse = await api.post('/bookings/', bookingPayload);
      const booking = bookingResponse.data;

      // Step 2: Process payment
      // Map frontend payment method to backend enum values
      const paymentMethodMap = {
        'card': 'Card',
        'upi': 'UPI',
        'netbanking': 'NetBanking',
        'wallet': 'Wallet'
      };
      
      const paymentPayload = {
        booking_reference: booking.booking_reference,
        amount: booking.total_fare,
        method: paymentMethodMap[paymentMethod] || paymentMethod,
      };

      const paymentResponse = await api.post('/payments/', paymentPayload);
      const confirmedBooking = paymentResponse.data;

      // Navigate to confirmation page
      navigate(`/booking/confirmation/${confirmedBooking.pnr}`, {
        state: { booking: confirmedBooking },
        replace: true,
      });

    } catch (err) {
      console.error('Booking error:', err);
      setError(err.response?.data?.detail || 'Failed to complete booking. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Format card number with spaces
  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    return parts.length ? parts.join(' ') : v;
  };

  // Show loading while checking auth
  if (authLoading || loading) {
    return (
      <div className="booking-page">
        <Navbar />
        <div className="booking-loading">
          <Loader2 className="spinner" size={48} />
          <p>Loading booking details...</p>
        </div>
        <Footer />
      </div>
    );
  }

  // Show error if no flight
  if (error && !flight) {
    return (
      <div className="booking-page">
        <Navbar />
        <div className="booking-error-page">
          <AlertCircle size={64} />
          <h2>Unable to Load Booking</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/flights')} className="btn btn-primary">
            Search Flights
          </button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="booking-page">
      <Navbar />
      
      <main className="booking-main">
        <div className="booking-container">
          {/* Back to Search Button - Only visible on Step 1 */}
          {currentStep === 1 && (
            <button 
              className="back-to-search-btn"
              onClick={() => navigate('/flights')}
            >
              <ArrowLeft size={18} />
              Back to Flight Search
            </button>
          )}

          {/* Progress Steps */}
          <div className="booking-steps">
            {STEPS.map((step, index) => (
              <div 
                key={step.id}
                className={`step ${currentStep >= step.id ? 'active' : ''} ${currentStep > step.id ? 'completed' : ''}`}
              >
                <div className="step-indicator">
                  {currentStep > step.id ? (
                    <CheckCircle size={24} />
                  ) : (
                    <step.icon size={24} />
                  )}
                </div>
                <span className="step-name">{step.name}</span>
                {index < STEPS.length - 1 && <ChevronRight className="step-arrow" />}
              </div>
            ))}
          </div>

          <div className="booking-content">
            {/* Left: Form Content */}
            <div className="booking-form-section">
              {error && (
                <div className="booking-error">
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </div>
              )}

              {/* Step 1: Passenger Details */}
              {currentStep === 1 && (
                <div className="step-content">
                  <div className="step-header">
                    <div>
                      <h2>Passenger Details</h2>
                      <p className="step-description">Enter details for all {passengers.length} passenger(s)</p>
                    </div>
                    <button 
                      type="button" 
                      className="add-passenger-btn"
                      onClick={addPassenger}
                      disabled={passengers.length >= 9}
                    >
                      <Plus size={18} />
                      Add Passenger
                    </button>
                  </div>

                  {passengers.map((passenger, index) => (
                    <div key={index} className="passenger-card">
                      <div className="passenger-header">
                        <User size={20} />
                        <span>Passenger {index + 1}</span>
                        {index === 0 && <span className="primary-badge">Primary</span>}
                        {passengers.length > 1 && (
                          <button 
                            type="button" 
                            className="remove-passenger-btn"
                            onClick={() => removePassenger(index)}
                            title="Remove passenger"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>

                      <div className="passenger-form">
                        <div className="form-group">
                          <label>Full Name (as per ID)</label>
                          <input
                            type="text"
                            value={passenger.passenger_name}
                            onChange={(e) => handlePassengerChange(index, 'passenger_name', e.target.value)}
                            placeholder="Enter full name"
                            required
                          />
                        </div>

                        <div className="form-row">
                          <div className="form-group">
                            <label>Age</label>
                            <input
                              type="number"
                              value={passenger.age}
                              onChange={(e) => handlePassengerChange(index, 'age', e.target.value)}
                              placeholder="Age"
                              min="1"
                              max="120"
                              required
                            />
                          </div>

                          <div className="form-group">
                            <label>Gender</label>
                            <select
                              value={passenger.gender}
                              onChange={(e) => handlePassengerChange(index, 'gender', e.target.value)}
                              required
                            >
                              <option value="">Select</option>
                              <option value="M">Male</option>
                              <option value="F">Female</option>
                              <option value="O">Other</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Step 2: Select Seats */}
              {currentStep === 2 && (
                <div className="step-content">
                  <h2>Select Your Seats</h2>
                  <p className="step-description">
                    Choose preferred seats for each passenger. Window and aisle seats have additional surcharges.
                  </p>

                  <SeatSelector
                    flightId={parseInt(flightId)}
                    seatClass={seatTier}
                    passengerCount={passengers.length}
                    passengers={passengers}
                    selectedSeats={selectedSeats}
                    onSeatSelect={handleSeatSelect}
                    basePrice={tierPrice}
                  />
                </div>
              )}

              {/* Step 3: Review Booking */}
              {currentStep === 3 && (
                <div className="step-content">
                  <h2>Review Your Booking</h2>
                  <p className="step-description">Please verify all details before proceeding to payment</p>

                  {/* Flight Summary */}
                  <div className="review-section">
                    <h3>Flight Details</h3>
                    <div className="review-flight">
                      <div className="flight-header">
                        <Plane size={24} />
                        <span className="flight-number">{flight.flight_number}</span>
                        <span className="airline-name">{flight.airline_name || flight.airline}</span>
                      </div>
                      
                      <div className="flight-route">
                        <div className="route-point">
                          <span className="city">{flight.departure_city || flight.source}</span>
                          <span className="code">{flight.departure_airport_code || flight.source}</span>
                          <span className="time">
                            {new Date(flight.departure_time).toLocaleTimeString('en-IN', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
                          <span className="date">
                            {new Date(flight.departure_time).toLocaleDateString('en-IN', {
                              weekday: 'short',
                              day: 'numeric',
                              month: 'short'
                            })}
                          </span>
                        </div>
                        
                        <div className="route-line">
                          <div className="line"></div>
                          <Plane size={16} />
                        </div>
                        
                        <div className="route-point">
                          <span className="city">{flight.arrival_city || flight.destination}</span>
                          <span className="code">{flight.arrival_airport_code || flight.destination}</span>
                          <span className="time">
                            {new Date(flight.arrival_time).toLocaleTimeString('en-IN', { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </span>
                          <span className="date">
                            {new Date(flight.arrival_time).toLocaleDateString('en-IN', {
                              weekday: 'short',
                              day: 'numeric',
                              month: 'short'
                            })}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flight-meta">
                        <span className="tier-badge">{seatTier.replace('_', ' ')}</span>
                      </div>
                    </div>
                  </div>

                  {/* Passengers & Seats Summary */}
                  <div className="review-section">
                    <h3>Passengers & Seats ({passengers.length})</h3>
                    <div className="passengers-list">
                      {passengers.map((p, index) => (
                        <div key={index} className="passenger-summary">
                          <User size={18} />
                          <div className="passenger-info">
                            <span className="name">{p.passenger_name}</span>
                            <span className="details">
                              {p.age} yrs, {p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : 'Other'}
                              {selectedSeats[index] && (
                                <> • Seat {selectedSeats[index].seat_number} ({selectedSeats[index].seat_position})</>
                              )}
                            </span>
                          </div>
                          {selectedSeats[index]?.surcharge > 0 && (
                            <span className="seat-surcharge-badge">+₹{selectedSeats[index].surcharge.toFixed(0)}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Price Breakdown */}
                  <div className="review-section">
                    <h3>Fare Summary</h3>
                    <div className="fare-breakdown">
                      <div className="fare-row">
                        <span>Base Fare ({seatTier.replace('_', ' ')}) × {passengers.length}</span>
                        <span>₹{tierPrice.toFixed(2)} × {passengers.length}</span>
                      </div>
                      {seatSurcharge > 0 && (
                        <div className="fare-row">
                          <span>Seat Selection Surcharge</span>
                          <span>+₹{seatSurcharge.toFixed(2)}</span>
                        </div>
                      )}
                      <div className="fare-row">
                        <span>Taxes & Fees</span>
                        <span>Included</span>
                      </div>
                      <div className="fare-row total">
                        <span>Total Amount</span>
                        <span>₹{totalPrice.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Payment */}
              {currentStep === 4 && (
                <div className="step-content">
                  <h2>Payment</h2>
                  <p className="step-description">Choose your preferred payment method</p>

                  {/* Payment Methods */}
                  <div className="payment-methods">
                    <label className={`payment-method ${paymentMethod === 'card' ? 'active' : ''}`}>
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="card"
                        checked={paymentMethod === 'card'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                      />
                      <CreditCard size={24} />
                      <span>Credit/Debit Card</span>
                    </label>

                    <label className={`payment-method ${paymentMethod === 'upi' ? 'active' : ''}`}>
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="upi"
                        checked={paymentMethod === 'upi'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                      />
                      <IndianRupee size={24} />
                      <span>UPI</span>
                    </label>

                    <label className={`payment-method ${paymentMethod === 'netbanking' ? 'active' : ''}`}>
                      <input
                        type="radio"
                        name="paymentMethod"
                        value="netbanking"
                        checked={paymentMethod === 'netbanking'}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                      />
                      <Shield size={24} />
                      <span>Net Banking</span>
                    </label>
                  </div>

                  {/* Card Payment Form */}
                  {paymentMethod === 'card' && (
                    <div className="payment-form">
                      <div className="form-group">
                        <label>Card Number</label>
                        <input
                          type="text"
                          value={cardDetails.number}
                          onChange={(e) => setCardDetails(prev => ({
                            ...prev,
                            number: formatCardNumber(e.target.value)
                          }))}
                          placeholder="1234 5678 9012 3456"
                          maxLength="19"
                        />
                      </div>

                      <div className="form-group">
                        <label>Cardholder Name</label>
                        <input
                          type="text"
                          value={cardDetails.name}
                          onChange={(e) => setCardDetails(prev => ({
                            ...prev,
                            name: e.target.value.toUpperCase()
                          }))}
                          placeholder="NAME ON CARD"
                        />
                      </div>

                      <div className="form-row">
                        <div className="form-group">
                          <label>Expiry Date</label>
                          <input
                            type="text"
                            value={cardDetails.expiry}
                            onChange={(e) => {
                              let value = e.target.value.replace(/\D/g, '');
                              if (value.length >= 2) {
                                value = value.substring(0, 2) + '/' + value.substring(2, 4);
                              }
                              setCardDetails(prev => ({ ...prev, expiry: value }));
                            }}
                            placeholder="MM/YY"
                            maxLength="5"
                          />
                        </div>

                        <div className="form-group">
                          <label>CVV</label>
                          <input
                            type="password"
                            value={cardDetails.cvv}
                            onChange={(e) => setCardDetails(prev => ({
                              ...prev,
                              cvv: e.target.value.replace(/\D/g, '').substring(0, 4)
                            }))}
                            placeholder="•••"
                            maxLength="4"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* UPI Payment Form */}
                  {paymentMethod === 'upi' && (
                    <div className="payment-form">
                      <div className="form-group">
                        <label>UPI ID</label>
                        <input
                          type="text"
                          value={upiId}
                          onChange={(e) => setUpiId(e.target.value)}
                          placeholder="yourname@upi"
                        />
                      </div>
                    </div>
                  )}

                  {/* Net Banking */}
                  {paymentMethod === 'netbanking' && (
                    <div className="payment-form">
                      <div className="form-group">
                        <label>Select Bank</label>
                        <select 
                          value={selectedBank}
                          onChange={(e) => setSelectedBank(e.target.value)}
                        >
                          <option value="">Choose your bank</option>
                          <option value="sbi">State Bank of India</option>
                          <option value="hdfc">HDFC Bank</option>
                          <option value="icici">ICICI Bank</option>
                          <option value="axis">Axis Bank</option>
                          <option value="kotak">Kotak Mahindra Bank</option>
                          <option value="pnb">Punjab National Bank</option>
                          <option value="bob">Bank of Baroda</option>
                          <option value="canara">Canara Bank</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {/* Security Note */}
                  <div className="security-note">
                    <Shield size={18} />
                    <span>Your payment is secured with 256-bit SSL encryption</span>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="booking-actions">
                {currentStep > 1 && (
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={handleBack}
                    disabled={submitting}
                  >
                    <ArrowLeft size={18} />
                    Back
                  </button>
                )}

                {currentStep < 4 ? (
                  <button 
                    type="button" 
                    className="btn btn-primary"
                    onClick={handleNext}
                  >
                    Continue
                    <ArrowRight size={18} />
                  </button>
                ) : (
                  <button 
                    type="button" 
                    className="btn btn-primary pay-btn"
                    onClick={handleSubmit}
                    disabled={submitting}
                  >
                    {submitting ? (
                      <>
                        Processing...
                      </>
                    ) : (
                      <>
                        Pay ₹{totalPrice.toFixed(2)}
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Right: Booking Summary Sidebar */}
            <div className="booking-sidebar">
              <div className="sidebar-card">
                <h3>Booking Summary</h3>
                
                {flight && (
                  <>
                    <div className="summary-flight">
                      <div className="summary-route">
                        <span className="from">{flight.departure_city || flight.source}</span>
                        <Plane size={16} />
                        <span className="to">{flight.arrival_city || flight.destination}</span>
                      </div>
                      <div className="summary-date">
                        <Calendar size={14} />
                        {new Date(flight.departure_time).toLocaleDateString('en-IN', {
                          weekday: 'long',
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })}
                      </div>
                      <div className="summary-time">
                        <Clock size={14} />
                        {new Date(flight.departure_time).toLocaleTimeString('en-IN', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                        {' - '}
                        {new Date(flight.arrival_time).toLocaleTimeString('en-IN', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    </div>

                    <div className="summary-details">
                      <div className="detail-row">
                        <span>Flight</span>
                        <span>{flight.flight_number}</span>
                      </div>
                      <div className="detail-row">
                        <span>Class</span>
                        <span>{seatTier.replace('_', ' ')}</span>
                      </div>
                      <div className="detail-row">
                        <span>Passengers</span>
                        <span>{passengers.length} Adult(s)</span>
                      </div>
                      {selectedSeats.length > 0 && (
                        <div className="detail-row">
                          <span>Seats</span>
                          <span>{selectedSeats.map(s => s.seat_number).join(', ')}</span>
                        </div>
                      )}
                    </div>

                    <div className="summary-price">
                      <div className="price-row">
                        <span>Base Fare × {passengers.length}</span>
                        <span>₹{baseTotalPrice.toFixed(2)}</span>
                      </div>
                      {seatSurcharge > 0 && (
                        <div className="price-row surcharge">
                          <span>Seat Surcharge</span>
                          <span>+₹{seatSurcharge.toFixed(2)}</span>
                        </div>
                      )}
                      <div className="price-row total">
                        <span>Total</span>
                        <span>₹{totalPrice.toFixed(2)}</span>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="sidebar-info">
                <p>✓ Free cancellation within 24 hours</p>
                <p>✓ Instant e-ticket confirmation</p>
                <p>✓ 24/7 customer support</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default BookingPage;
