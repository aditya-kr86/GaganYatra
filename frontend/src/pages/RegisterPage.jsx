import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Plane, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2,
  User, Phone, Globe, CheckCircle, ArrowLeft, ArrowRight, RefreshCw
} from 'lucide-react';
import './AuthPages.css';

const COUNTRIES = [
  'India', 'United States', 'United Kingdom', 'Canada', 'Australia',
  'Germany', 'France', 'Japan', 'Singapore', 'UAE', 'Other'
];

const STEPS = {
  EMAIL: 1,
  OTP: 2,
  DETAILS: 3,
};

const RegisterPage = () => {
  const [step, setStep] = useState(STEPS.EMAIL);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    mobile: '',
    country: '',
    password: '',
    confirmPassword: '',
    otp: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  
  // OTP input refs for auto-focus
  const otpRefs = useRef([]);

  const { register, sendOTP, verifyOTP } = useAuth();
  const navigate = useNavigate();

  // Countdown timer for resend OTP
  useEffect(() => {
    let interval;
    if (resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [resendTimer]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  // Handle OTP input
  const handleOTPChange = (index, value) => {
    if (!/^\d*$/.test(value)) return; // Only digits
    
    const newOTP = formData.otp.split('');
    newOTP[index] = value;
    setFormData(prev => ({ ...prev, otp: newOTP.join('') }));
    
    // Auto-focus next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
    setError('');
  };

  const handleOTPKeyDown = (index, e) => {
    // Handle backspace
    if (e.key === 'Backspace' && !formData.otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOTPPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    setFormData(prev => ({ ...prev, otp: pastedData }));
    
    // Focus the last filled input or the next empty one
    const focusIndex = Math.min(pastedData.length, 5);
    otpRefs.current[focusIndex]?.focus();
  };

  // Step 1: Send OTP
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!formData.email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      const result = await sendOTP(formData.email);
      if (result.success) {
        setOtpSent(true);
        setStep(STEPS.OTP);
        setResendTimer(60); // 60 seconds cooldown
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResendOTP = async () => {
    if (resendTimer > 0) return;
    
    setLoading(true);
    setError('');
    try {
      const result = await sendOTP(formData.email);
      if (result.success) {
        setResendTimer(60);
        setFormData(prev => ({ ...prev, otp: '' }));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to resend OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    if (formData.otp.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const result = await verifyOTP(formData.email, formData.otp);
      if (result.success) {
        setStep(STEPS.DETAILS);
      } else {
        setError(result.error || result.message);
      }
    } catch (err) {
      setError('OTP verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Validate final form
  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (!/[A-Z]/.test(formData.password)) {
      setError('Password must contain at least one uppercase letter');
      return false;
    }
    if (!/[a-z]/.test(formData.password)) {
      setError('Password must contain at least one lowercase letter');
      return false;
    }
    if (!/[0-9]/.test(formData.password)) {
      setError('Password must contain at least one number');
      return false;
    }
    if (formData.mobile && !/^\+?[1-9]\d{9,14}$/.test(formData.mobile.replace(/\s/g, ''))) {
      setError('Please enter a valid mobile number (10-15 digits)');
      return false;
    }
    return true;
  };

  // Step 3: Complete Registration
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) return;

    setLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      const result = await register(registerData);
      
      if (result.success) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-success-container">
          <div className="success-content">
            <CheckCircle className="success-icon" size={64} />
            <h2>Registration Successful!</h2>
            <p>Your account has been created. Redirecting to login...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container register-container">
        <div className="auth-left">
          <div className="auth-branding">
            <Link to="/" className="auth-logo">
              <Plane className="auth-logo-icon" />
              <span>FlightBooker</span>
            </Link>
            <h1>Join FlightBooker</h1>
            <p>Create an account to start booking flights and manage your travel</p>
          </div>
          
          {/* Progress Steps */}
          <div className="registration-steps">
            <div className={`reg-step ${step >= STEPS.EMAIL ? 'active' : ''} ${step > STEPS.EMAIL ? 'completed' : ''}`}>
              <div className="step-number">{step > STEPS.EMAIL ? <CheckCircle size={16} /> : '1'}</div>
              <span>Email</span>
            </div>
            <div className="step-line"></div>
            <div className={`reg-step ${step >= STEPS.OTP ? 'active' : ''} ${step > STEPS.OTP ? 'completed' : ''}`}>
              <div className="step-number">{step > STEPS.OTP ? <CheckCircle size={16} /> : '2'}</div>
              <span>Verify OTP</span>
            </div>
            <div className="step-line"></div>
            <div className={`reg-step ${step >= STEPS.DETAILS ? 'active' : ''}`}>
              <div className="step-number">3</div>
              <span>Details</span>
            </div>
          </div>

          <div className="auth-features">
            <div className="auth-feature">
              <span className="feature-icon">🔐</span>
              <span>OTP verified registration</span>
            </div>
            <div className="auth-feature">
              <span className="feature-icon">🔒</span>
              <span>Secure booking process</span>
            </div>
            <div className="auth-feature">
              <span className="feature-icon">💳</span>
              <span>Easy payment options</span>
            </div>
            <div className="auth-feature">
              <span className="feature-icon">📧</span>
              <span>Instant e-tickets</span>
            </div>
          </div>
        </div>

        <div className="auth-right">
          <div className="auth-form-container">
            <Link to="/" className="auth-back-btn">
              <ArrowLeft size={18} />
              Back to Home
            </Link>
            
            {/* Step 1: Email */}
            {step === STEPS.EMAIL && (
              <>
                <h2>Get Started</h2>
                <p className="auth-subtitle">Enter your email to receive a verification code</p>

                {error && (
                  <div className="auth-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSendOTP} className="auth-form">
                  <div className="form-group">
                    <label htmlFor="email">Email Address</label>
                    <div className="input-wrapper">
                      <Mail className="input-icon" size={18} />
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="Enter your email"
                        required
                        autoFocus
                      />
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    className="auth-submit-btn"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spinner" size={18} />
                        Sending OTP...
                      </>
                    ) : (
                      <>
                        Send Verification Code
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </form>
              </>
            )}

            {/* Step 2: OTP Verification */}
            {step === STEPS.OTP && (
              <>
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setStep(STEPS.EMAIL)}
                >
                  <ArrowLeft size={18} />
                  Back
                </button>
                
                <h2>Verify Your Email</h2>
                <p className="auth-subtitle">
                  We've sent a 6-digit code to<br />
                  <strong>{formData.email}</strong>
                </p>

                {error && (
                  <div className="auth-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleVerifyOTP} className="auth-form">
                  <div className="form-group">
                    <label>Enter OTP</label>
                    <div className="otp-inputs" onPaste={handleOTPPaste}>
                      {[0, 1, 2, 3, 4, 5].map((index) => (
                        <input
                          key={index}
                          ref={el => otpRefs.current[index] = el}
                          type="text"
                          maxLength={1}
                          value={formData.otp[index] || ''}
                          onChange={(e) => handleOTPChange(index, e.target.value)}
                          onKeyDown={(e) => handleOTPKeyDown(index, e)}
                          className="otp-input"
                          autoFocus={index === 0}
                        />
                      ))}
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    className="auth-submit-btn"
                    disabled={loading || formData.otp.length !== 6}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spinner" size={18} />
                        Verifying...
                      </>
                    ) : (
                      <>
                        Verify & Continue
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>

                  <div className="resend-otp">
                    {resendTimer > 0 ? (
                      <span className="resend-timer">
                        Resend OTP in {resendTimer}s
                      </span>
                    ) : (
                      <button 
                        type="button" 
                        className="resend-btn"
                        onClick={handleResendOTP}
                        disabled={loading}
                      >
                        <RefreshCw size={16} />
                        Resend OTP
                      </button>
                    )}
                  </div>
                </form>
              </>
            )}

            {/* Step 3: Complete Details */}
            {step === STEPS.DETAILS && (
              <>
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setStep(STEPS.OTP)}
                >
                  <ArrowLeft size={18} />
                  Back
                </button>

                <h2>Complete Your Profile</h2>
                <p className="auth-subtitle">Fill in your details to create your account</p>

                {error && (
                  <div className="auth-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="first_name">First Name</label>
                      <div className="input-wrapper">
                        <User className="input-icon" size={18} />
                        <input
                          type="text"
                          id="first_name"
                          name="first_name"
                          value={formData.first_name}
                          onChange={handleChange}
                          placeholder="First name"
                          required
                          minLength={2}
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label htmlFor="last_name">Last Name</label>
                      <div className="input-wrapper">
                        <User className="input-icon" size={18} />
                        <input
                          type="text"
                          id="last_name"
                          name="last_name"
                          value={formData.last_name}
                          onChange={handleChange}
                          placeholder="Last name"
                          required
                          minLength={2}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="verified-email">
                    <Mail size={16} />
                    <span>{formData.email}</span>
                    <CheckCircle size={16} className="verified-icon" />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="mobile">Mobile Number</label>
                      <div className="input-wrapper">
                        <Phone className="input-icon" size={18} />
                        <input
                          type="tel"
                          id="mobile"
                          name="mobile"
                          value={formData.mobile}
                          onChange={handleChange}
                          placeholder="+91 9876543210"
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label htmlFor="country">Country</label>
                      <div className="input-wrapper">
                        <Globe className="input-icon" size={18} />
                        <select
                          id="country"
                          name="country"
                          value={formData.country}
                          onChange={handleChange}
                        >
                          <option value="">Select country</option>
                          {COUNTRIES.map(country => (
                            <option key={country} value={country}>{country}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <div className="input-wrapper">
                      <Lock className="input-icon" size={18} />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        id="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="Create a password"
                        required
                        minLength={8}
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <p className="password-hint">
                      Min 8 characters with uppercase, lowercase, and number
                    </p>
                  </div>

                  <div className="form-group">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <div className="input-wrapper">
                      <Lock className="input-icon" size={18} />
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        id="confirmPassword"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="Confirm your password"
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="form-group terms">
                    <label className="checkbox-label">
                      <input type="checkbox" required />
                      <span>
                        I agree to the{' '}
                        <Link to="/terms">Terms of Service</Link>
                        {' '}and{' '}
                        <Link to="/privacy">Privacy Policy</Link>
                      </span>
                    </label>
                  </div>

                  <button 
                    type="submit" 
                    className="auth-submit-btn"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spinner" size={18} />
                        Creating account...
                      </>
                    ) : (
                      'Create Account'
                    )}
                  </button>
                </form>
              </>
            )}

            <div className="auth-divider">
              <span>or</span>
            </div>

            <p className="auth-switch">
              Already have an account?{' '}
              <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
