/**
 * Hook for handling job description input (URL or text)
 */

import { useState, useCallback } from 'react';
import { extractJobFromURL, extractJobFromText, getErrorMessage } from '@/lib/api';
import type { JobRequirements } from '@/types';

interface UseJobInputReturn {
  jobText: string;
  setJobText: (text: string) => void;
  jobData: JobRequirements | null;
  isProcessing: boolean;
  error: string | null;
  submitJob: () => Promise<void>;
  clearError: () => void;
  clearJob: () => void;
}

const isValidURL = (string: string): boolean => {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch (_) {
    return false;
  }
};

export const useJobInput = (): UseJobInputReturn => {
  const [jobText, setJobText] = useState('');
  const [jobData, setJobData] = useState<JobRequirements | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitJob = useCallback(async () => {
    if (!jobText.trim()) {
      setError('Please enter a job URL or description');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setJobData(null);

    try {
      const trimmedText = jobText.trim();
      const isURL = isValidURL(trimmedText);

      let response;
      if (isURL) {
        // Extract from URL
        response = await extractJobFromURL({ urls: [trimmedText] });
      } else {
        // Extract from text
        response = await extractJobFromText({ job_text: trimmedText });
      }

      if (response.success && response.job_data) {
        setJobData(response.job_data);
      } else {
        setError(response.message || 'Failed to process job information');
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      console.error('Job extraction error:', err);
    } finally {
      setIsProcessing(false);
    }
  }, [jobText]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearJob = useCallback(() => {
    setJobText('');
    setJobData(null);
    setError(null);
  }, []);

  return {
    jobText,
    setJobText,
    jobData,
    isProcessing,
    error,
    submitJob,
    clearError,
    clearJob,
  };
};

