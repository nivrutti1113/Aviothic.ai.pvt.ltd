import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import api from '../api';

function Navigation() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Try to get user info to verify authentication
      api.get('/auth/me')
        .then(response => {
          setIsAuthenticated(true);
          setUser(response.data);
        })
        .catch(() => {
          setIsAuthenticated(false);
          setUser(null);
        });
    }
  }, [location]); // Re-check when route changes

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Even if logout API fails, clear local tokens
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      setIsAuthenticated(false);
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <nav style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '1rem 2rem', 
      backgroundColor: '#f8f9fa', 
      borderBottom: '1px solid #dee2e6' 
    }}>
      <div>
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Aviothic.ai</h1>
        </Link>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {isAuthenticated ? (
          <>
            <span>Welcome, {user?.full_name || user?.email}</span>
            <span>Role: {user?.role || 'user'}</span>
            <div style={{ display: 'flex', gap: '1rem' }}>
              {user?.role === 'user' && (
                <Link to="/dashboard" style={{ textDecoration: 'none', color: '#007bff' }}>Dashboard</Link>
              )}
              {(user?.role === 'doctor' || user?.role === 'admin') && (
                <Link to="/doctor" style={{ textDecoration: 'none', color: '#007bff' }}>Doctor Portal</Link>
              )}
              {user?.role === 'admin' && (
                <Link to="/admin" style={{ textDecoration: 'none', color: '#dc3545' }}>Admin Panel</Link>
              )}
            </div>
            <button 
              onClick={handleLogout}
              style={{ 
                backgroundColor: '#dc3545', 
                color: 'white', 
                border: 'none', 
                padding: '5px 10px', 
                borderRadius: '4px', 
                cursor: 'pointer' 
              }}
            >
              Logout
            </button>
          </>
        ) : (
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to="/login" style={{ textDecoration: 'none', color: '#007bff' }}>Login</Link>
            <Link to="/signup" style={{ textDecoration: 'none', color: '#28a745' }}>Sign Up</Link>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navigation;