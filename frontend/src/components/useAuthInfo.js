import { useAuth, useUser } from '@clerk/clerk-react';

// Custom hook to get authentication information
export function useAuthInfo() {
  const { isSignedIn, userId, sessionId } = useAuth();
  const { user } = useUser();
  
  return {
    isSignedIn,
    userId,
    sessionId,
    user,
    userEmail: user?.emailAddresses?.[0]?.emailAddress,
    userName: user?.firstName ? `${user.firstName} ${user.lastName || ''}`.trim() : null,
    userRole: user?.publicMetadata?.role || 'user', // Default role
  };
}

// Custom hook to check if user has specific roles
export function useHasRole(requiredRole) {
  const { userRole } = useAuthInfo();
  
  // For simplicity, we're just checking if the user has the required role
  // In a real app, you might have more complex role hierarchies
  return userRole === requiredRole || userRole === 'admin';
}

export default useAuthInfo;