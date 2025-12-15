/**
 * Hook for handling job description input (URL or text)
 */

import { useState, useCallback, useEffect } from 'react';
import { extractJobFromURL, extractJobFromText, updateSessionJob, getErrorMessage } from '@/lib/api';
import type { JobRequirements } from '@/types';

interface UseJobInputProps {
  sessionId: string | null;
  onJobSubmitted?: () => void;
}

interface UseJobInputReturn {
  jobUrl: string;
  setJobUrl: (url: string) => void;
  jobText: string;
  setJobText: (text: string) => void;
  jobData: JobRequirements | null;
  isProcessing: boolean;
  error: string | null;
  urlValidationError: string | null;
  textValidationError: string | null;
  isValidInput: boolean;
  submitJob: () => Promise<void>;
  clearError: () => void;
  clearJob: () => void;
}

const isValidURL = (string: string): boolean => {
  if (!string.trim()) return false;
  try {
    const url = new URL(string.trim());
    // Check protocol (must be http or https)
    const hasValidProtocol: boolean = url.protocol === 'http:' || url.protocol === 'https:';
    // Check host (must exist and not be empty)
    const hasValidHost: boolean = Boolean(url.hostname && url.hostname.length > 0 && url.hostname.trim().length > 0);
    // Host should contain at least one dot (for domain) or be localhost (for development)
    const hasValidHostFormat: boolean = url.hostname.includes('.') || url.hostname === 'localhost';
    
    return hasValidProtocol && hasValidHost && hasValidHostFormat;
  } catch (_) {
    return false;
  }
};

const MIN_TEXT_LENGTH = 50;

export const useJobInput = ({ sessionId, onJobSubmitted }: UseJobInputProps): UseJobInputReturn => {
  const [jobUrl, setJobUrl] = useState('');
  const [jobText, setJobText] = useState('');
  const [jobData, setJobData] = useState<JobRequirements | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [urlValidationError, setUrlValidationError] = useState<string | null>(null);
  const [textValidationError, setTextValidationError] = useState<string | null>(null);

  // Validate URL on change
  useEffect(() => {
    if (jobUrl.trim()) {
      if (isValidURL(jobUrl)) {
        setUrlValidationError(null);
      } else {
        setUrlValidationError('Please enter a valid URL with http:// or https:// and a valid domain name');
      }
    } else {
      setUrlValidationError(null);
    }
  }, [jobUrl]);

  // Validate text on change
  useEffect(() => {
    if (jobText.trim()) {
      if (jobText.trim().length < MIN_TEXT_LENGTH) {
        setTextValidationError(`Please enter at least ${MIN_TEXT_LENGTH} characters`);
      } else {
        setTextValidationError(null);
      }
    } else {
      setTextValidationError(null);
    }
  }, [jobText]);

  // Check if at least one valid input exists
  const isValidInput = isValidURL(jobUrl) || (jobText.trim().length >= MIN_TEXT_LENGTH);

  const submitJob = useCallback(async () => {
    const hasValidUrl = isValidURL(jobUrl);
    const hasValidText = jobText.trim().length >= MIN_TEXT_LENGTH;

    if (!hasValidUrl && !hasValidText) {
      setError('Please enter a valid job URL or at least 50 characters of job description');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setJobData(null);

    try {
      let response;
      if (hasValidUrl) {
        // Extract from URL (prioritize URL if both are provided)
        response = await extractJobFromURL({ urls: [jobUrl.trim()] });
      } else {
        // Extract from text
        response = await extractJobFromText({ job_text: jobText.trim() });
      }

      if (response.success && response.job_data) {
        setJobData(response.job_data);
        
        // Update supervisor session with job data
        if (sessionId) {
          try {
            await updateSessionJob(sessionId, response.job_data);
            onJobSubmitted?.();
          } catch (updateError) {
            // Don't fail the submission if session update fails
            console.warn('Failed to update supervisor session:', updateError);
          }
        }
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
  }, [jobUrl, jobText, sessionId, onJobSubmitted]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearJob = useCallback(() => {
    setJobUrl('');
    setJobText('');
    setJobData(null);
    setError(null);
    setUrlValidationError(null);
    setTextValidationError(null);
  }, []);

  return {
    jobUrl,
    setJobUrl,
    jobText,
    setJobText,
    jobData,
    isProcessing,
    error,
    urlValidationError,
    textValidationError,
    isValidInput,
    submitJob,
    clearError,
    clearJob,
  };
};

