import React, { useState } from 'react';
import api from '../api';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container" style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>Upload Medical Image</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <input 
          type="file" 
          onChange={handleFileChange} 
          accept="image/*" 
          style={{ marginBottom: '10px' }}
        />
        <br />
        <button 
          type="submit" 
          disabled={!file || loading}
          style={{ 
            backgroundColor: '#3B82F6', 
            color: 'white', 
            padding: '10px 15px', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: 'pointer'
          }}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>
      
      {error && (
        <div style={{ color: 'red', marginBottom: '20px' }}>
          Error: {error}
        </div>
      )}

      {result && (
        <div className="result" style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '15px', marginTop: '20px' }}>
          <h3>Analysis Result</h3>
          <p><strong>Prediction:</strong> {result.prediction}</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(2)}%</p>
            <p><strong>Risk Score:</strong> {result.risk_score}/100</p>
            <p><strong>BI-RADS:</strong> Category {result.birads_class}</p>
            <p><strong>Lesion Type:</strong> {result.lesion_type}</p>
            <p><strong>Breast Density:</strong> {result.breast_density}</p>
          </div>
          <p><strong>Explanation:</strong> {result.explanation}</p>
          
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            {result.image_url && (
              <div>
                <p>Original Image:</p>
                <img src={result.image_url} alt="Uploaded" style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
              </div>
            )}
            <div>
              <p>Grad-CAM:</p>
              <img src={result.gradcam_url} alt="Grad-CAM" style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
            </div>
          </div>
          
          <div style={{ marginTop: '15px' }}>
            <a href={result.report_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6', textDecoration: 'underline' }}>
              Download PDF Report
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;