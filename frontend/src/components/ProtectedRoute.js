import React from 'react';
import { useAuth } from '@clerk/clerk-react';
import { Navigate } from 'react-router-dom';
import Login from './Login';

function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth();

  // Show loading state while checking auth status
  if (!isLoaded) {
    return <div>Loading...</div>;
  }

  // If user is not signed in, redirect to login
  if (!isSignedIn) {
    return <Login />;
  }

  // If user is signed in, show the protected content
  return <>{children}</>;
}

export default ProtectedRoute;