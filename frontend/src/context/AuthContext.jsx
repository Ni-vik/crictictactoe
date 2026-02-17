import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Optional: Verify token availability or decode it
      // For now, we assume if token exists, user is logged in (until 401)
      // You might want to decode JWT to get username if needed
      // setUser({ token }); 
    }
    setLoading(false);
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', {
          username_or_email: username,
          password: password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser({ username }); // We assume username for now
      return true;
    } catch (error) {
      console.error("Login failed", error);
      return false;
    }
  };

  const signup = async (username, email, password) => {
    try {
        const payload = { username, password };
        if (email && email.trim() !== "") {
            payload.email = email;
        }
        
        await api.post('/auth/signup', payload);
        return true;
    } catch (error) {
        console.error("Signup failed", error);
        const errorMessage = error.response?.data?.detail;
        if (Array.isArray(errorMessage)) {
            // Handle Pydantic validation errors (often a list)
            throw new Error(errorMessage.map(e => e.msg).join(', '));
        }
        throw new Error(errorMessage || "Signup failed. Please check your inputs.");
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, signup, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
