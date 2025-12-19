import React, { useState } from 'react';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (caseId) => {
    try {
      const response = await fetch(`/report/${caseId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Error downloading report: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>Aviothic.ai — Upload Medical Image</h2>
      
      <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="image-upload">Select Medical Image:</label>
          <input 
            id="image-upload"
            type="file" 
            accept="image/*" 
            onChange={handleFileChange} 
            style={{ marginLeft: '10px' }}
          />
        </div>
        <button 
          type="submit" 
          disabled={loading || !file}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: loading || !file ? 'not-allowed' : 'pointer',
            opacity: loading || !file ? 0.6 : 1
          }}
        >
          {loading ? 'Analyzing...' : 'Analyze Image'}
        </button>
      </form>

      {error && (
        <div style={{ 
          color: 'red', 
          marginBottom: '20px', 
          padding: '10px', 
          backgroundColor: '#f8d7da', 
          border: '1px solid #f5c6cb', 
          borderRadius: '4px' 
        }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ 
          marginTop: '20px', 
          padding: '20px', 
          backgroundColor: '#f8f9fa', 
          border: '1px solid #dee2e6', 
          borderRadius: '4px' 
        }}>
          <h3>Analysis Results</h3>
          <div style={{ marginBottom: '10px' }}>
            <strong>Case ID:</strong> {result.case_id}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Prediction:</strong> {result.prediction}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Confidence:</strong> {(Math.max(...result.probabilities) * 100).toFixed(2)}%
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Model Version:</strong> {result.model_version}
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>Timestamp:</strong> {new Date(result.timestamp).toLocaleString()}
          </div>
          <button 
            onClick={() => handleDownloadReport(result.case_id)}
            style={{ 
              padding: '8px 16px', 
              backgroundColor: '#28a745', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Download Report
          </button>
        </div>
      )}
    </div>
  );
}

export default UploadPage;