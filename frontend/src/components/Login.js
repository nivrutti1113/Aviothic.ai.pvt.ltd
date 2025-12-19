import React from 'react';
import { useSignIn } from '@clerk/clerk-react';
import { SignIn } from '@clerk/clerk-react';

function Login() {
  return (
    <div className="login-container" style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Aviothic.ai Login</h2>
      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
        <SignIn 
          appearance={{
            elements: {
              formButtonPrimary: 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded',
            }
          }}
        />
      </div>
    </div>
  );
}

export default Login;