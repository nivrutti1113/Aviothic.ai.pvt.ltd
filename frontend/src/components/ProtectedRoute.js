import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

function ProtectedRoute({ children, requiredRole }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setIsAuthenticated(false);
        return;
      }
      
      try {
        // Verify token by getting user info
        const response = await api.get('/auth/me');
        setIsAuthenticated(true);
        setUserRole(response.data.role);
      } catch (error) {
        // Token might be expired, try to refresh
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          try {
            const refreshResponse = await api.post('/auth/refresh', {
              refresh_token: refreshToken
            });
            
            localStorage.setItem('token', refreshResponse.data.access_token);
            if (refreshResponse.data.refresh_token) {
              localStorage.setItem('refreshToken', refreshResponse.data.refresh_token);
            }
            
            // Now try to get user info again
            const userInfoResponse = await api.get('/auth/me');
            setIsAuthenticated(true);
            setUserRole(userInfoResponse.data.role);
          } catch (refreshError) {
            setIsAuthenticated(false);
          }
        } else {
          setIsAuthenticated(false);
        }
      }
    };
    
    checkAuth();
  }, []);

  // Show loading state while checking auth status
  if (isAuthenticated === null) {
    return <div>Loading...</div>;
  }

  // If user is not authenticated, redirect to login
  if (!isAuthenticated) {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    navigate('/login');
    return null;
  }
  
  // Check role if required
  if (requiredRole && userRole !== requiredRole) {
    navigate('/'); // Redirect to home if user doesn't have required role
    return null;
  }

  // If user is authenticated, show the protected content
  return <>{children}</>;
}

export default ProtectedRoute;