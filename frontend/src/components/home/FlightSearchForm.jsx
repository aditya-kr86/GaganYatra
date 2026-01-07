import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Calendar, Users, Search, ArrowRightLeft, Loader2 } from 'lucide-react';
import { airportAPI } from '../../api/flights';

const FlightSearchForm = () => {
  const navigate = useNavigate();
  const [airports, setAirports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    origin: '',
    destination: '',
    date: '',
    passengers: 1,
    tripType: 'oneway',
    travelClass: 'ECONOMY',
  });

  // Fetch airports on mount
  useEffect(() => {
    const fetchAirports = async () => {
      try {
        const data = await airportAPI.getAllAirports();
        setAirports(data);
      } catch (error) {
        console.error('Failed to fetch airports:', error);
      }
    };
    fetchAirports();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const swapLocations = () => {
    setFormData(prev => ({
      ...prev,
      origin: prev.destination,
      destination: prev.origin,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Build query params
    const params = new URLSearchParams({
      origin: formData.origin,
      destination: formData.destination,
      date: formData.date,
      passengers: formData.passengers,
      tier: formData.travelClass,
    });
    
    navigate(`/flights?${params.toString()}`);
    setLoading(false);
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="search-form-container">
      <div className="search-form-header">
        <h2>Find Your Perfect Flight</h2>
        <div className="trip-type-toggle">
          <button
            type="button"
            className={`trip-btn ${formData.tripType === 'oneway' ? 'active' : ''}`}
            onClick={() => setFormData(prev => ({ ...prev, tripType: 'oneway' }))}
          >
            One Way
          </button>
          <button
            type="button"
            className={`trip-btn ${formData.tripType === 'roundtrip' ? 'active' : ''}`}
            onClick={() => setFormData(prev => ({ ...prev, tripType: 'roundtrip' }))}
          >
            Round Trip
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="form-row">
          {/* Origin */}
          <div className="form-group">
            <label>
              <MapPin size={16} />
              From
            </label>
            <select
              name="origin"
              value={formData.origin}
              onChange={handleChange}
              required
            >
              <option value="">Select Origin</option>
              {airports.map(airport => (
                <option key={airport.id} value={airport.code}>
                  {airport.code} - {airport.city}
                </option>
              ))}
            </select>
          </div>

          {/* Swap Button */}
          <button 
            type="button" 
            className="swap-btn"
            onClick={swapLocations}
            title="Swap locations"
          >
            <ArrowRightLeft size={20} />
          </button>

          {/* Destination */}
          <div className="form-group">
            <label>
              <MapPin size={16} />
              To
            </label>
            <select
              name="destination"
              value={formData.destination}
              onChange={handleChange}
              required
            >
              <option value="">Select Destination</option>
              {airports.map(airport => (
                <option key={airport.id} value={airport.code}>
                  {airport.code} - {airport.city}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          {/* Date */}
          <div className="form-group">
            <label>
              <Calendar size={16} />
              Departure Date
            </label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              min={today}
              required
            />
          </div>

          {/* Passengers */}
          <div className="form-group">
            <label>
              <Users size={16} />
              Passengers
            </label>
            <select
              name="passengers"
              value={formData.passengers}
              onChange={handleChange}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                <option key={num} value={num}>
                  {num} {num === 1 ? 'Passenger' : 'Passengers'}
                </option>
              ))}
            </select>
          </div>

          {/* Travel Class */}
          <div className="form-group">
            <label>Class</label>
            <select
              name="travelClass"
              value={formData.travelClass}
              onChange={handleChange}
            >
              <option value="ECONOMY">Economy</option>
              <option value="ECONOMY_FLEX">Economy Flex</option>
              <option value="BUSINESS">Business</option>
              <option value="FIRST">First Class</option>
            </select>
          </div>
        </div>

        <button 
          type="submit" 
          className="search-btn"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="spinner" size={20} />
              Searching...
            </>
          ) : (
            <>
              <Search size={20} />
              Search Flights
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default FlightSearchForm;
