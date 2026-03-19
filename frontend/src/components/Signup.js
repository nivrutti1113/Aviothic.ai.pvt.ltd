import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function Signup() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    hospital: '',
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
      await api.post('/auth/register', {
        full_name: formData.full_name,
        email: formData.email,
        hospital: formData.hospital,
        password: formData.password
      });
      
      // Redirect to login after successful signup
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="signup-container" style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Aviothic.ai Sign Up</h2>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="text"
            name="full_name"
            placeholder="Full Name"
            value={formData.full_name}
            onChange={handleChange}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
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
            type="text"
            name="hospital"
            placeholder="Hospital (optional)"
            value={formData.hospital}
            onChange={handleChange}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            name="password"
            placeholder="Password (min 8 characters)"
            value={formData.password}
            onChange={handleChange}
            required
            minLength="8"
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <button 
          type="submit" 
          style={{ 
            backgroundColor: '#10B981', 
            color: 'white', 
            padding: '10px 15px', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer',
            width: '100%'
          }}
        >
          Sign Up
        </button>
      </form>
      <div style={{ marginTop: '10px', textAlign: 'center' }}>
        Already have an account? <a href="/login" style={{ color: '#3B82F6' }}>Login</a>
      </div>
    </div>
  );
}

export default Signup;