import React from 'react';
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react';

// Replace with your actual publishable key from Clerk dashboard
const publishableKey = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY || 'pk_test_YOUR_PUBLISHABLE_KEY';

function AuthProvider({ children }) {
  if (!publishableKey) {
    console.error('Missing Publishable Key');
    return (
      <div className="error">
        Missing Clerk Publishable Key. Please add REACT_APP_CLERK_PUBLISHABLE_KEY to your environment variables.
      </div>
    );
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      {children}
    </ClerkProvider>
  );
}

export default AuthProvider;