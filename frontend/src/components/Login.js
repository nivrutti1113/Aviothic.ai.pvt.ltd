import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/auth/login', {
        email: formData.email,
        password: formData.password
      });
      
      // Store tokens in localStorage
      localStorage.setItem('token', response.data.access_token);
      if (response.data.refresh_token) {
        localStorage.setItem('refreshToken', response.data.refresh_token);
      }
      
      // Navigate based on role
      const tokenPayload = JSON.parse(atob(response.data.access_token.split('.')[1]));
      const userRole = tokenPayload.role;
      
      if (userRole === 'admin') {
        navigate('/admin');
      } else if (userRole === 'doctor') {
        navigate('/doctor');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="login-container" style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Aviothic.ai Login</h2>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <button 
          type="submit" 
          style={{ 
            backgroundColor: '#3B82F6', 
            color: 'white', 
            padding: '10px 15px', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer',
            width: '100%'
          }}
        >
          Login
        </button>
      </form>
      <div style={{ marginTop: '15px', textAlign: 'center' }}>
        <a href="/forgot-password" style={{ color: '#3B82F6' }}>Forgot Password?</a>
      </div>
      <div style={{ marginTop: '10px', textAlign: 'center' }}>
        Don't have an account? <a href="/signup" style={{ color: '#3B82F6' }}>Sign Up</a>
      </div>
    </div>
  );
}

export default Login;