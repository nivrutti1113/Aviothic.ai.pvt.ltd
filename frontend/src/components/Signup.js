import React from 'react';
import { SignUp } from '@clerk/clerk-react';

function Signup() {
  return (
    <div className="signup-container" style={{ padding: '20px', maxWidth: '400px', margin: '0 auto' }}>
      <h2>Create Aviothic.ai Account</h2>
      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
        <SignUp 
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

export default Signup;