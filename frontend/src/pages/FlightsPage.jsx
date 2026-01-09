import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../api/config';
import { 
  Search, Plane, Calendar, Users, MapPin, Clock, ArrowRight, 
  Filter, ChevronDown, Loader2, AlertCircle
} from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './FlightsPage.css';

const SEAT_CLASSES = [
  { value: 'ECONOMY', label: 'Economy', short: 'ECO' },
  { value: 'BUSINESS', label: 'Business', short: 'BUS' },
  { value: 'FIRST', label: 'First', short: 'FST' },
];

const FlightsPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Search form state
  const [origin, setOrigin] = useState(searchParams.get('origin') || '');
  const [destination, setDestination] = useState(searchParams.get('destination') || '');
  const [date, setDate] = useState(searchParams.get('date') || '');
  const [passengers, setPassengers] = useState(parseInt(searchParams.get('passengers')) || 1);
  
  // Data state
  const [flights, setFlights] = useState([]);
  const [airports, setAirports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  
  // Selected class per flight (key: flight.id, value: tier)
  const [selectedClasses, setSelectedClasses] = useState({});
  
  // Filter state
  const [sortBy, setSortBy] = useState('price');
  const [filterAirline, setFilterAirline] = useState('all');

  // Fetch airports for dropdowns
  useEffect(() => {
    const fetchAirports = async () => {
      try {
        const response = await api.get('/airports');
        setAirports(response.data);
      } catch (err) {
        console.error('Failed to fetch airports:', err);
      }
    };
    fetchAirports();
  }, []);

  // Auto-search if URL has params
  useEffect(() => {
    if (searchParams.get('origin') && searchParams.get('destination')) {
      handleSearch();
    }
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    
    if (!origin || !destination) {
      setError('Please select origin and destination');
      return;
    }
    
    setLoading(true);
    setError('');
    setSearched(true);

    try {
      const params = new URLSearchParams({
        origin,
        destination,
        ...(date && { date }),
        passengers: passengers.toString(),
        tier: 'all',  // Fetch all class prices
      });

      const response = await api.get(`/flights/search?${params}`);
      setFlights(response.data);
      
      // Initialize selected class to ECONOMY for each flight
      const initialClasses = {};
      response.data.forEach(f => {
        initialClasses[f.id] = 'ECONOMY';
      });
      setSelectedClasses(initialClasses);
      
      // Update URL
      navigate(`/flights?${params}`, { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search flights');
      setFlights([]);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', { 
      weekday: 'short', 
      day: 'numeric', 
      month: 'short' 
    });
  };

  const calculateDuration = (departure, arrival) => {
    const diff = new Date(arrival) - new Date(departure);
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  // Get unique airlines for filter
  const airlines = [...new Set(flights.map(f => f.airline?.name || f.airline).filter(Boolean))];

  // Get display price for a flight based on selected class
  const getFlightPrice = (flight, tier) => {
    if (flight.price_map && flight.price_map[tier]) {
      return flight.price_map[tier];
    }
    return flight.dynamic_price || flight.current_price || flight.base_price || 0;
  };

  // Sort and filter flights
  const filteredFlights = flights
    .filter(f => filterAirline === 'all' || (f.airline?.name || f.airline) === filterAirline)
    .sort((a, b) => {
      if (sortBy === 'price') {
        const priceA = getFlightPrice(a, selectedClasses[a.id] || 'ECONOMY');
        const priceB = getFlightPrice(b, selectedClasses[b.id] || 'ECONOMY');
        return priceA - priceB;
      }
      if (sortBy === 'duration') {
        const durationA = new Date(a.arrival_time) - new Date(a.departure_time);
        const durationB = new Date(b.arrival_time) - new Date(b.departure_time);
        return durationA - durationB;
      }
      if (sortBy === 'departure') return new Date(a.departure_time) - new Date(b.departure_time);
      return 0;
    });

  // Handle class selection for a flight
  const handleClassSelect = (flightId, tier) => {
    setSelectedClasses(prev => ({ ...prev, [flightId]: tier }));
  };

  return (
    <>
      <Navbar />
      <div className="flights-page">
        {/* Search Section */}
        <section className="flights-search">
          <div className="search-container">
            <h1>Find Your Flight</h1>
            <form onSubmit={handleSearch} className="search-form">
              <div className="search-row">
                <div className="search-field">
                  <label>From</label>
                  <div className="input-wrapper">
                    <MapPin size={18} />
                    <select value={origin} onChange={(e) => setOrigin(e.target.value)} required>
                      <option value="">Select Origin</option>
                      {airports.map(airport => (
                        <option key={airport.id} value={airport.code}>
                          {airport.code} - {airport.city}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <button type="button" className="swap-btn" onClick={() => {
                  const temp = origin;
                  setOrigin(destination);
                  setDestination(temp);
                }}>
                  ⇄
                </button>
                
                <div className="search-field">
                  <label>To</label>
                  <div className="input-wrapper">
                    <MapPin size={18} />
                    <select value={destination} onChange={(e) => setDestination(e.target.value)} required>
                      <option value="">Select Destination</option>
                      {airports.map(airport => (
                        <option key={airport.id} value={airport.code}>
                          {airport.code} - {airport.city}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="search-field">
                  <label>Date</label>
                  <div className="input-wrapper">
                    <Calendar size={18} />
                    <input 
                      type="date" 
                      value={date} 
                      onChange={(e) => setDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                </div>
                
                <div className="search-field small">
                  <label>Passengers</label>
                  <div className="input-wrapper">
                    <Users size={18} />
                    <select value={passengers} onChange={(e) => setPassengers(parseInt(e.target.value))}>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <button type="submit" className="search-btn" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="spinner" size={20} />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search size={20} />
                      Search
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </section>

        {/* Results Section */}
        <section className="flights-results">
          <div className="results-container">
            {error && (
              <div className="error-message">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            {searched && !loading && flights.length > 0 && (
              <>
                <div className="results-header">
                  <div className="results-count">
                    <span>{filteredFlights.length} flights found</span>
                    <span className="route-info">
                      {origin} → {destination}
                      {date && ` • ${formatDate(date)}`}
                    </span>
                  </div>
                  <div className="results-filters">
                    <div className="filter-group">
                      <Filter size={16} />
                      <select value={filterAirline} onChange={(e) => setFilterAirline(e.target.value)}>
                        <option value="all">All Airlines</option>
                        {airlines.map(airline => (
                          <option key={airline} value={airline}>{airline}</option>
                        ))}
                      </select>
                    </div>
                    <div className="filter-group">
                      <span>Sort by:</span>
                      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                        <option value="price">Price</option>
                        <option value="duration">Duration</option>
                        <option value="departure">Departure Time</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flights-list">
                  {filteredFlights.map((flight) => {
                    const selectedTier = selectedClasses[flight.id] || 'ECONOMY';
                    const selectedPrice = getFlightPrice(flight, selectedTier);
                    const totalForAll = selectedPrice * passengers;
                    
                    // Check seats available for selected class
                    const seatsForSelectedClass = flight.seats_by_class?.[selectedTier] ?? 0;
                    const isBookingDisabled = seatsForSelectedClass < passengers;
                    
                    // Check if any class has seats available
                    const hasAnySeatsAvailable = SEAT_CLASSES.some(
                      cls => (flight.seats_by_class?.[cls.value] ?? 0) > 0
                    );
                    
                    return (
                      <div key={flight.id} className="flight-card">
                        <div className="flight-main-info">
                          <div className="flight-airline">
                            <div className="airline-logo">
                              <Plane size={24} />
                            </div>
                            <div className="airline-info">
                              <span className="airline-name">{flight.airline || 'Airline'}</span>
                              <span className="flight-number">{flight.flight_number}</span>
                            </div>
                          </div>

                          <div className="flight-times">
                            <div className="time-block">
                              <span className="time">{formatTime(flight.departure_time)}</span>
                              <span className="airport">{flight.source || origin}</span>
                            </div>
                            <div className="flight-duration">
                              <span className="duration-time">
                                {calculateDuration(flight.departure_time, flight.arrival_time)}
                              </span>
                              <div className="duration-line">
                                <Plane size={16} />
                              </div>
                              <span className="stops">Direct</span>
                            </div>
                            <div className="time-block">
                              <span className="time">{formatTime(flight.arrival_time)}</span>
                              <span className="airport">{flight.destination || destination}</span>
                            </div>
                          </div>
                        </div>

                        {/* Class Selection Grid */}
                        <div className="class-selection">
                          <div className="class-options">
                            {SEAT_CLASSES.map((cls) => {
                              const classPrice = getFlightPrice(flight, cls.value);
                              const isSelected = selectedTier === cls.value;
                              const seatsForClass = flight.seats_by_class?.[cls.value] ?? flight.seats_left ?? 0;
                              const showSeatsWarning = seatsForClass < 10;
                              
                              return (
                                <button
                                  key={cls.value}
                                  className={`class-option ${isSelected ? 'selected' : ''} ${seatsForClass === 0 ? 'sold-out' : ''}`}
                                  onClick={() => seatsForClass > 0 && handleClassSelect(flight.id, cls.value)}
                                  disabled={seatsForClass === 0}
                                >
                                  <span className="class-name">{cls.label}</span>
                                  <span className="class-price">₹{classPrice?.toLocaleString()}</span>
                                  {seatsForClass === 0 ? (
                                    <span className="class-soldout">Sold Out</span>
                                  ) : showSeatsWarning ? (
                                    <span className="class-seats-warning">{seatsForClass} left</span>
                                  ) : (
                                    <span className="class-per">per person</span>
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        {/* Booking Section */}
                        <div className="flight-booking">
                          <div className="total-price">
                            <span className="total-label">
                              Total for {passengers} passenger{passengers > 1 ? 's' : ''}
                            </span>
                            <span className="total-amount">₹{totalForAll?.toLocaleString()}</span>
                          </div>
                          <button 
                            className="book-btn"
                            onClick={() => navigate(`/booking/new?flight=${flight.id}&passengers=${passengers}&tier=${selectedTier}&price=${selectedPrice}`)}
                            disabled={isBookingDisabled}
                            title={isBookingDisabled ? `Not enough seats available (${seatsForSelectedClass} left, need ${passengers})` : ''}
                          >
                            {isBookingDisabled ? (
                              seatsForSelectedClass === 0 ? 'Sold Out' : `Only ${seatsForSelectedClass} left`
                            ) : (
                              <>Book {SEAT_CLASSES.find(c => c.value === selectedTier)?.label}</>
                            )}
                            {!isBookingDisabled && <ArrowRight size={16} />}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}

            {searched && !loading && flights.length === 0 && !error && (
              <div className="no-flights">
                <Plane size={64} />
                <h2>No Flights Found</h2>
                <p>Try adjusting your search criteria or selecting different dates</p>
              </div>
            )}

            {!searched && !loading && (
              <div className="search-prompt">
                <Plane size={64} />
                <h2>Search for Flights</h2>
                <p>Enter your travel details above to find available flights</p>
              </div>
            )}

            {loading && (
              <div className="loading-state">
                <Loader2 className="spinner" size={48} />
                <p>Searching for the best flights...</p>
              </div>
            )}
          </div>
        </section>
      </div>
      <Footer />
    </>
  );
};

export default FlightsPage;
