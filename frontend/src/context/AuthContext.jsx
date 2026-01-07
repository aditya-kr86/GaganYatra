import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/config';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          // Verify token by fetching user profile
          const response = await api.get('/auth/me', {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          setUser(response.data);
          setToken(storedToken);
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      return { success: false, error: message };
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      return { success: true, user: response.data };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      return { success: false, error: message };
    }
  };

  // Send OTP for registration
  const sendOTP = async (email) => {
    try {
      const response = await api.post('/auth/send-otp', { email });
      return { success: true, message: response.data.message };
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to send OTP';
      return { success: false, error: message };
    }
  };

  // Verify OTP
  const verifyOTP = async (email, otp) => {
    try {
      const response = await api.post('/auth/verify-otp', { email, otp });
      return { success: response.data.success, message: response.data.message };
    } catch (error) {
      const message = error.response?.data?.detail || 'OTP verification failed';
      return { success: false, error: message };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await api.post('/auth/logout', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      // Ignore logout errors
    }
    
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  // Update profile function
  const updateProfile = async (profileData) => {
    try {
      const response = await api.put('/users/profile', profileData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      return { success: true, user: response.data };
    } catch (error) {
      const message = error.response?.data?.detail || 'Update failed';
      return { success: false, error: message };
    }
  };

  // Change password function
  const changePassword = async (currentPassword, newPassword) => {
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Password change failed';
      return { success: false, error: message };
    }
  };

  // Check if user has a specific role
  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  // Check if user is admin
  const isAdmin = () => hasRole('admin');

  // Check if user is airline staff
  const isAirlineStaff = () => hasRole('airline_staff');

  // Check if user is airport authority
  const isAirportAuthority = () => hasRole('airport_authority');

  // Check if user is any type of staff
  const isStaff = () => hasRole(['admin', 'airline_staff', 'airport_authority']);

  // Check if user is authenticated
  const isAuthenticated = () => !!user && !!token;

  const value = {
    user,
    token,
    loading,
    login,
    register,
    sendOTP,
    verifyOTP,
    logout,
    updateProfile,
    changePassword,
    hasRole,
    isAdmin,
    isAirlineStaff,
    isAirportAuthority,
    isStaff,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
