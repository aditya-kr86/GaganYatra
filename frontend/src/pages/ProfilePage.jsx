import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  User, Mail, Phone, Globe, Lock, Save, AlertCircle, CheckCircle, Loader2
} from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './ProfilePage.css';

const ProfilePage = () => {
  const { user, updateProfile, changePassword, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    mobile: '',
    country: '',
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated()) {
      navigate('/login', { state: { from: { pathname: '/profile' } } });
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        mobile: user.mobile || '',
        country: user.country || '',
      });
    }
  }, [user]);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
    setProfileError('');
    setProfileSuccess('');
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    setPasswordError('');
    setPasswordSuccess('');
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileError('');
    setProfileSuccess('');

    const result = await updateProfile({
      first_name: profileData.first_name,
      last_name: profileData.last_name,
      mobile: profileData.mobile,
      country: profileData.country,
    });

    if (result.success) {
      setProfileSuccess('Profile updated successfully!');
    } else {
      setProfileError(result.error);
    }
    setProfileLoading(false);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordLoading(true);
    setPasswordError('');
    setPasswordSuccess('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('Passwords do not match');
      setPasswordLoading(false);
      return;
    }

    if (passwordData.new_password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      setPasswordLoading(false);
      return;
    }

    const result = await changePassword(
      passwordData.current_password,
      passwordData.new_password
    );

    if (result.success) {
      setPasswordSuccess('Password changed successfully!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } else {
      setPasswordError(result.error);
    }
    setPasswordLoading(false);
  };

  if (authLoading) {
    return (
      <div className="profile-loading">
        <Loader2 className="spinner" size={48} />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="profile-page">
        <div className="profile-container">
          <div className="profile-header">
            <div className="profile-avatar">
              <User size={48} />
            </div>
            <div className="profile-info">
              <h1>{user?.first_name} {user?.last_name}</h1>
              <p>{user?.email}</p>
              <span className="profile-role">{user?.role}</span>
            </div>
          </div>

          <div className="profile-sections">
            {/* Profile Information */}
            <section className="profile-section">
              <h2>Profile Information</h2>
              
              {profileError && (
                <div className="message error">
                  <AlertCircle size={18} />
                  <span>{profileError}</span>
                </div>
              )}
              
              {profileSuccess && (
                <div className="message success">
                  <CheckCircle size={18} />
                  <span>{profileSuccess}</span>
                </div>
              )}

              <form onSubmit={handleProfileSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="first_name">First Name</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="first_name"
                        name="first_name"
                        value={profileData.first_name}
                        onChange={handleProfileChange}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="last_name">Last Name</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="last_name"
                        name="last_name"
                        value={profileData.last_name}
                        onChange={handleProfileChange}
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email Address</label>
                  <div className="input-wrapper">
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={profileData.email}
                      disabled
                      className="disabled"
                    />
                  </div>
                  <p className="form-hint">Email cannot be changed</p>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="mobile">Mobile Number</label>
                    <div className="input-wrapper">
                      <input
                        type="tel"
                        id="mobile"
                        name="mobile"
                        value={profileData.mobile}
                        onChange={handleProfileChange}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="country">Country</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="country"
                        name="country"
                        value={profileData.country}
                        onChange={handleProfileChange}
                      />
                    </div>
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="save-btn"
                  disabled={profileLoading}
                >
                  {profileLoading ? (
                    <>
                      <Loader2 className="spinner" size={18} />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={18} />
                      Save Changes
                    </>
                  )}
                </button>
              </form>
            </section>

            {/* Change Password */}
            <section className="profile-section">
              <h2>Change Password</h2>
              
              {passwordError && (
                <div className="message error">
                  <AlertCircle size={18} />
                  <span>{passwordError}</span>
                </div>
              )}
              
              {passwordSuccess && (
                <div className="message success">
                  <CheckCircle size={18} />
                  <span>{passwordSuccess}</span>
                </div>
              )}

              <form onSubmit={handlePasswordSubmit}>
                <div className="form-group">
                  <label htmlFor="current_password">Current Password</label>
                  <div className="input-wrapper">
                    <input
                      type="password"
                      id="current_password"
                      name="current_password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      placeholder="Enter your current password"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="new_password">New Password</label>
                  <div className="input-wrapper">
                    <input
                      type="password"
                      id="new_password"
                      name="new_password"
                      value={passwordData.new_password}
                      onChange={handlePasswordChange}
                      placeholder="Enter your new password"
                      required
                      minLength={8}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="confirm_password">Confirm New Password</label>
                  <div className="input-wrapper">
                    <input
                      type="password"
                      id="confirm_password"
                      name="confirm_password"
                      value={passwordData.confirm_password}
                      onChange={handlePasswordChange}
                      placeholder="Confirm your new password"
                      required
                    />
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="save-btn secondary"
                  disabled={passwordLoading}
                >
                  {passwordLoading ? (
                    <>
                      <Loader2 className="spinner" size={18} />
                      Updating...
                    </>
                  ) : (
                    <>
                      <Lock size={18} />
                      Update Password
                    </>
                  )}
                </button>
              </form>
            </section>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default ProfilePage;
