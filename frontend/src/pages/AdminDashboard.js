import React, { useEffect, useState } from 'react';
import api from '../api';

function AdminDashboard() {
  const [predictions, setPredictions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch all predictions
        const predictionsResponse = await api.get('/admin/predictions');
        setPredictions(predictionsResponse.data);
        
        // Fetch all users
        const usersResponse = await api.get('/admin/users');
        setUsers(usersResponse.data);
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await api.delete(`/admin/user/${userId}`);
        // Refresh user list
        const usersResponse = await api.get('/admin/users');
        setUsers(usersResponse.data);
        alert('User deleted successfully');
      } catch (err) {
        alert(`Failed to delete user: ${err.message}`);
      }
    }
  };

  const handleApprovePrediction = async (caseId, status) => {
    try {
      await api.post('/admin/approve', {
        case_id: caseId,
        admin_status: status
      });
      
      // Refresh predictions list
      const predictionsResponse = await api.get('/admin/predictions');
      setPredictions(predictionsResponse.data);
      
      alert('Prediction status updated successfully');
    } catch (err) {
      alert(`Failed to update prediction: ${err.message}`);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: 20, fontFamily: 'Arial' }}>
      <h2>Admin Dashboard</h2>
      
      <div style={{ marginBottom: '30px' }}>
        <h3>All Predictions</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Case ID</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>User</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Prediction</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Confidence</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Risk Score</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Doctor Status</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map(prediction => (
              <tr key={prediction.id}>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{prediction.case_id.substring(0, 8)}...</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{prediction.user_id.substring(0, 8)}...</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{prediction.prediction}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{(prediction.confidence * 100).toFixed(2)}%</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{prediction.risk_score}/100</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{prediction.doctor_status || 'Pending'}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                  <select 
                    defaultValue={prediction.admin_status || ''}
                    onChange={(e) => handleApprovePrediction(prediction.case_id, e.target.value)}
                    style={{ marginRight: '5px' }}
                  >
                    <option value="">Set Status</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="pending">Pending</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div>
        <h3>Manage Users</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f2f2f2' }}>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Name</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Email</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Role</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Created</th>
              <th style={{ border: '1px solid #ddd', padding: '8px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{user.full_name}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{user.email}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{user.role}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{new Date(user.created_at).toLocaleDateString()}</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                  <button 
                    onClick={() => handleDeleteUser(user.id)}
                    style={{ 
                      backgroundColor: '#dc3545', 
                      color: 'white', 
                      border: 'none', 
                      padding: '5px 10px', 
                      borderRadius: '4px', 
                      cursor: 'pointer' 
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default AdminDashboard;