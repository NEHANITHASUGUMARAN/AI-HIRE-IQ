import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { GoogleOAuthProvider } from '@react-oauth/google'
import axios from 'axios'
import './index.css'
import App from './App.jsx'
import store from './app/store.js';
import { BrowserRouter as Router } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext.jsx'

// ✅ SAFE FALLBACKS
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const API_URL = import.meta.env.VITE_API_URL || "https://hire-iq-backend.onrender.com";

//axios.defaults.baseURL = API_URL;

axios.defaults.baseURL = import.meta.env.VITE_API_URL;

console.log("API URL:", import.meta.env.VITE_API_URL);

// ✅ Prevent crash if Google ID missing
const AppWrapper = () => {
  if (!GOOGLE_CLIENT_ID) {
    console.warn("Google Client ID missing");
    return (
      <Provider store={store}>
        <ThemeProvider>
          <Router>
            <App />
          </Router>
        </ThemeProvider>
      </Provider>
    );
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Provider store={store}>
        <ThemeProvider>
          <Router>
            <App />
          </Router>
        </ThemeProvider>
      </Provider>
    </GoogleOAuthProvider>
  );
};

// Axios interceptor
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!error.config.url.includes('login')) {
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

createRoot(document.getElementById('root')).render(<AppWrapper />);