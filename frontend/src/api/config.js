import axios from 'axios';

// API base URL - points to FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

console.log('🔗 API Base URL:', API_BASE_URL);

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // Increased timeout
});

// Request interceptor for logging/auth
api.interceptors.request.use(
  (config) => {
    console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`);
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error.message);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`📥 ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('❌ Request timeout - Backend may not be running');
    } else if (error.code === 'ERR_NETWORK') {
      console.error('❌ Network Error - Backend is not reachable at', API_BASE_URL);
    } else if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      console.warn('⚠️ Unauthorized - token cleared');
    } else {
      console.error('❌ API Error:', error.response?.status, error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// Health check function
export const checkAPIHealth = async () => {
  try {
    const response = await api.get('/health');
    console.log('✅ Backend is healthy:', response.data);
    return true;
  } catch (error) {
    console.error('❌ Backend health check failed:', error.message);
    return false;
  }
};

export default api;
export { API_BASE_URL };
