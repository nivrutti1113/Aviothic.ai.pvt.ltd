import React, { useEffect, useState } from 'react';
import api from '../api';

function DoctorDashboard() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [noteText, setNoteText] = useState({});
  const [statusSelection, setStatusSelection] = useState({});

  useEffect(() => {
    async function fetchCases() {
      try {
        const response = await api.get('/doctor/cases');
        setCases(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    fetchCases();
  }, []);

  const handleAddNote = async (caseId) => {
    try {
      await api.post('/doctor/add-note', {
        case_id: caseId,
        note: noteText[caseId] || '',
        status: statusSelection[caseId] || null
      });

      // Update local state to reflect changes
      setCases(prevCases => 
        prevCases.map(c => 
          c.case_id === caseId 
            ? { ...c, doctor_note: noteText[caseId], doctor_status: statusSelection[caseId] } 
            : c
        )
      );

      // Clear the input fields
      setNoteText(prev => ({ ...prev, [caseId]: '' }));
    } catch (err) {
      alert(`Failed to add note: ${err.message}`);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: 20, fontFamily: 'Arial' }}>
      <h2>Doctor Dashboard</h2>
      <h3>Pending Cases for Review</h3>
      {cases.length === 0 ? (
        <p>No pending cases for review.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '20px' }}>
          {cases.map(caseItem => (
            <div key={caseItem.id} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '15px' }}>
              <h4>Case: {caseItem.case_id}</h4>
              <p><strong>Prediction:</strong> {caseItem.prediction}</p>
              <p><strong>Confidence:</strong> {(caseItem.confidence * 100).toFixed(2)}%</p>
              <p><strong>Risk Score:</strong> {caseItem.risk_score}/100</p>
              <p><strong>Explanation:</strong> {caseItem.explanation}</p>
              
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <div>
                  <p>Original Image:</p>
                  <img src={caseItem.image_url} alt="Uploaded" style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
                </div>
                <div>
                  <p>Grad-CAM:</p>
                  <img src={caseItem.gradcam_url} alt="Grad-CAM" style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
                </div>
              </div>
              
              <div style={{ marginTop: '15px' }}>
                <textarea
                  placeholder="Add your notes here..."
                  value={noteText[caseItem.case_id] || ''}
                  onChange={(e) => setNoteText(prev => ({ ...prev, [caseItem.case_id]: e.target.value }))}
                  style={{ width: '100%', height: '80px', padding: '5px', boxSizing: 'border-box' }}
                />
              </div>
              
              <div style={{ marginTop: '10px' }}>
                <select
                  value={statusSelection[caseItem.case_id] || ''}
                  onChange={(e) => setStatusSelection(prev => ({ ...prev, [caseItem.case_id]: e.target.value }))}
                  style={{ marginRight: '10px', padding: '5px' }}
                >
                  <option value="">Select Status</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="rejected">Rejected</option>
                </select>
                <button 
                  onClick={() => handleAddNote(caseItem.case_id)}
                  style={{ 
                    backgroundColor: '#3B82F6', 
                    color: 'white', 
                    padding: '5px 10px', 
                    border: 'none', 
                    borderRadius: '4px', 
                    cursor: 'pointer'
                  }}
                >
                  Add Note & Update Status
                </button>
              </div>
              
              <div style={{ marginTop: '10px' }}>
                <a href={caseItem.report_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6', textDecoration: 'underline' }}>
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

export default DoctorDashboard;