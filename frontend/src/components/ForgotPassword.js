import React, { useState } from 'react';
import api from '../api';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/forgot-password', { email });
      setSubmitted(true);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset link');
    }
  };

  return (
    <div className="forgot-password-container" style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Forgot Password</h2>
      {!submitted ? (
        <>
          {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
          <form onSubmit={handleSubmit} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
            <div style={{ marginBottom: '15px' }}>
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
              />
            </div>
            <button 
              type="submit" 
              style={{ 
                backgroundColor: '#F59E0B', 
                color: 'white', 
                padding: '10px 15px', 
                border: 'none', 
                borderRadius: '4px', 
                cursor: 'pointer',
                width: '100%'
              }}
            >
              Send Reset Link
            </button>
          </form>
        </>
      ) : (
        <div>
          <p>If an account exists with this email, a reset link has been sent.</p>
          <p><a href="/login" style={{ color: '#3B82F6' }}>Back to Login</a></p>
        </div>
      )}
    </div>
  );
}

export default ForgotPassword;