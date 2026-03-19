import React, { useEffect, useState } from 'react';
import api from '../api';

function Dashboard() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchPredictions() {
      try {
        const response = await api.get('/user/history');
        setPredictions(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    fetchPredictions();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: 20, fontFamily: 'Arial' }}>
      <h2>User Dashboard</h2>
      <h3>Your Prediction History</h3>
      {predictions.length === 0 ? (
        <p>No predictions yet. Upload an image to get started.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {predictions.map(prediction => (
            <div key={prediction.id} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '15px' }}>
              <h4>Case: {prediction.case_id}</h4>
              <p><strong>Prediction:</strong> {prediction.prediction}</p>
              <p><strong>Confidence:</strong> {(prediction.confidence * 100).toFixed(2)}%</p>
              <p><strong>Risk Score:</strong> {prediction.risk_score}/100</p>
              <p><strong>Status:</strong> {prediction.doctor_status || 'Pending Review'}</p>
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <div>
                  <p>Original Image:</p>
                  <img src={prediction.image_url} alt="Uploaded" style={{ width: '100px', height: '100px', objectFit: 'cover' }} />
                </div>
                <div>
                  <p>Grad-CAM:</p>
                  <img src={prediction.gradcam_url} alt="Grad-CAM" style={{ width: '100px', height: '100px', objectFit: 'cover' }} />
                </div>
              </div>
              <div style={{ marginTop: '10px' }}>
                <a href={prediction.report_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6', textDecoration: 'underline' }}>
                  View PDF Report
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;