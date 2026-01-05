import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Plane, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2,
  CheckCircle, ArrowLeft, ArrowRight, RefreshCw, KeyRound
} from 'lucide-react';
import api from '../api/config';
import './AuthPages.css';

const STEPS = {
  EMAIL: 1,
  OTP: 2,
  NEW_PASSWORD: 3,
};

const ForgotPasswordPage = () => {
  const [step, setStep] = useState(STEPS.EMAIL);
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  
  // OTP input refs
  const otpRefs = useRef([]);
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

  // Handle OTP input
  const handleOTPChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOTP = otp.split('');
    newOTP[index] = value;
    setOtp(newOTP.join(''));
    
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
    setError('');
  };

  const handleOTPKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleOTPPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    setOtp(pastedData);
    const focusIndex = Math.min(pastedData.length, 5);
    otpRefs.current[focusIndex]?.focus();
  };

  // Step 1: Send OTP for password reset
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/auth/forgot-password', { email });
      if (response.data.success) {
        setStep(STEPS.OTP);
        setResendTimer(60);
      } else {
        setError(response.data.message || 'Failed to send OTP');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please try again.');
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
      const response = await api.post('/auth/forgot-password', { email });
      if (response.data.success) {
        setResendTimer(60);
        setOtp('');
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    if (otp.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/auth/verify-reset-otp', { email, otp });
      if (response.data.success) {
        setStep(STEPS.NEW_PASSWORD);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  // Validate password
  const validatePassword = () => {
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (!/[A-Z]/.test(newPassword)) {
      setError('Password must contain at least one uppercase letter');
      return false;
    }
    if (!/[a-z]/.test(newPassword)) {
      setError('Password must contain at least one lowercase letter');
      return false;
    }
    if (!/[0-9]/.test(newPassword)) {
      setError('Password must contain at least one number');
      return false;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    return true;
  };

  // Step 3: Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (!validatePassword()) return;

    setLoading(true);
    try {
      const response = await api.post('/auth/reset-password', { 
        email, 
        otp, 
        new_password: newPassword 
      });
      if (response.data.success) {
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password');
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
            <h2>Password Reset Successful!</h2>
            <p>Your password has been changed. Redirecting to login...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-left">
          <div className="auth-branding">
            <Link to="/" className="auth-logo">
              <Plane className="auth-logo-icon" />
              <span>FlightBooker</span>
            </Link>
            <h1>Forgot Password?</h1>
            <p>No worries! We'll help you reset your password securely.</p>
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
            <div className={`reg-step ${step >= STEPS.NEW_PASSWORD ? 'active' : ''}`}>
              <div className="step-number">3</div>
              <span>New Password</span>
            </div>
          </div>

          <div className="auth-features">
            <div className="auth-feature">
              <span className="feature-icon">🔐</span>
              <span>Secure OTP verification</span>
            </div>
            <div className="auth-feature">
              <span className="feature-icon">⏱️</span>
              <span>Quick password reset</span>
            </div>
            <div className="auth-feature">
              <span className="feature-icon">🛡️</span>
              <span>Your data is protected</span>
            </div>
          </div>
        </div>

        <div className="auth-right">
          <div className="auth-form-container">
            {/* Step 1: Email */}
            {step === STEPS.EMAIL && (
              <>
                <h2>Reset Password</h2>
                <p className="auth-subtitle">Enter your registered email to receive a verification code</p>

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
                        value={email}
                        onChange={(e) => { setEmail(e.target.value); setError(''); }}
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

                <p className="auth-switch">
                  Remember your password?{' '}
                  <Link to="/login">Sign in</Link>
                </p>
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
                  <strong>{email}</strong>
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
                          value={otp[index] || ''}
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
                    disabled={loading || otp.length !== 6}
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

            {/* Step 3: New Password */}
            {step === STEPS.NEW_PASSWORD && (
              <>
                <button 
                  type="button" 
                  className="back-btn"
                  onClick={() => setStep(STEPS.OTP)}
                >
                  <ArrowLeft size={18} />
                  Back
                </button>

                <h2>Create New Password</h2>
                <p className="auth-subtitle">Choose a strong password for your account</p>

                {error && (
                  <div className="auth-error">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                  </div>
                )}

                <form onSubmit={handleResetPassword} className="auth-form">
                  <div className="verified-email">
                    <Mail size={16} />
                    <span>{email}</span>
                    <CheckCircle size={16} className="verified-icon" />
                  </div>

                  <div className="form-group">
                    <label htmlFor="newPassword">New Password</label>
                    <div className="input-wrapper">
                      <Lock className="input-icon" size={18} />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        id="newPassword"
                        value={newPassword}
                        onChange={(e) => { setNewPassword(e.target.value); setError(''); }}
                        placeholder="Create new password"
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
                    <label htmlFor="confirmPassword">Confirm New Password</label>
                    <div className="input-wrapper">
                      <Lock className="input-icon" size={18} />
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        id="confirmPassword"
                        value={confirmPassword}
                        onChange={(e) => { setConfirmPassword(e.target.value); setError(''); }}
                        placeholder="Confirm new password"
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

                  <button 
                    type="submit" 
                    className="auth-submit-btn"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spinner" size={18} />
                        Resetting Password...
                      </>
                    ) : (
                      <>
                        <KeyRound size={18} />
                        Reset Password
                      </>
                    )}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
