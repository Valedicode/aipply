/**
 * Hook for managing supervisor session state
 */

import { useState, useEffect, useCallback } from 'react';
import { startSupervisorSession, isAPIError } from '@/lib/api';
import type { SupervisorSessionState } from '@/types';

interface UseSessionReturn {
  sessionId: string | null;
  sessionState: SupervisorSessionState | null;
  isInitializing: boolean;
  error: string | null;
  initializeSession: () => Promise<void>;
  updateSessionState: (state: SupervisorSessionState) => void;
  resetSession: () => void;
}

export const useSession = (): UseSessionReturn => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<SupervisorSessionState | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = useCallback(async () => {
    if (sessionId) return; // Already initialized

    setIsInitializing(true);
    setError(null);

    try {
      const response = await startSupervisorSession();
      
      if (response.success) {
        setSessionId(response.session_id);
        
        // Initialize session state
        setSessionState({
          session_stage: 'init',
          has_cv_data: false,
          has_job_data: false,
          has_company_data: false,
          needs_clarification: false,
          ready_for_writer: false,
          current_agent: 'supervisor',
        });
      } else {
        setError('Failed to initialize session');
      }
    } catch (err) {
      const errorMessage = isAPIError(err) 
        ? err.message 
        : 'Failed to connect to backend';
      setError(errorMessage);
      console.error('Session initialization error:', err);
    } finally {
      setIsInitializing(false);
    }
  }, [sessionId]);

  const updateSessionState = useCallback((state: SupervisorSessionState) => {
    setSessionState(state);
  }, []);

  const resetSession = useCallback(() => {
    setSessionId(null);
    setSessionState(null);
    setError(null);
    // Re-initialize
    initializeSession();
  }, [initializeSession]);

  return {
    sessionId,
    sessionState,
    isInitializing,
    error,
    initializeSession,
    updateSessionState,
    resetSession,
  };
};

