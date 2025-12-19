import React from 'react';
import { useAuth, useUser, UserButton } from '@clerk/clerk-react';
import { Link } from 'react-router-dom';

function Navigation() {
  const { isSignedIn } = useAuth();
  const { user } = useUser();

  return (
    <nav style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '1rem 2rem', 
      backgroundColor: '#f8f9fa', 
      borderBottom: '1px solid #dee2e6' 
    }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Aviothic.ai</h1>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {isSignedIn ? (
          <>
            <span>Welcome, {user?.firstName || user?.emailAddresses[0]?.emailAddress}</span>
            <UserButton 
              appearance={{
                elements: {
                  userButtonAvatarBox: {
                    width: '32px',
                    height: '32px',
                  }
                }
              }}
            />
          </>
        ) : (
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to="/login" style={{ textDecoration: 'none', color: '#007bff' }}>Login</Link>
            <Link to="/signup" style={{ textDecoration: 'none', color: '#28a745' }}>Sign Up</Link>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navigation;