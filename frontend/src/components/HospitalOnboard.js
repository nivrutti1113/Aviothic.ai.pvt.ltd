import React, { useState } from 'react';
import axios from 'axios';

const HospitalOnboard = () => {
  const [hospitalData, setHospitalData] = useState({
    name: '',
    address: '',
    contactEmail: '',
    contactPhone: ''
  });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setHospitalData({
      ...hospitalData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    try {
      // In a real implementation, this would call your backend API
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      setSuccess(true);
    } catch (err) {
      setError('Failed to onboard hospital. Please try again.');
    }
  };

  return (
    <div className="hospital-onboard">
      <h2>Hospital Onboarding</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">Hospital Name:</label>
          <input
            type="text"
            id="name"
            name="name"
            value={hospitalData.name}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label htmlFor="address">Address:</label>
          <textarea
            id="address"
            name="address"
            value={hospitalData.address}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label htmlFor="contactEmail">Contact Email:</label>
          <input
            type="email"
            id="contactEmail"
            name="contactEmail"
            value={hospitalData.contactEmail}
            onChange={handleChange}
            required
          />
        </div>
        <div>
          <label htmlFor="contactPhone">Contact Phone:</label>
          <input
            type="tel"
            id="contactPhone"
            name="contactPhone"
            value={hospitalData.contactPhone}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit">Onboard Hospital</button>
      </form>

      {success && (
        <div className="success-message">
          Hospital successfully onboarded!
        </div>
      )}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
};

export default HospitalOnboard;