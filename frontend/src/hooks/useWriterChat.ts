/**
 * Hook for managing Writer agent chat sessions
 * 
 * Replaces useSession and useChat hooks with a unified Writer chat interface.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { startWriterChat, sendWriterMessage, getErrorMessage } from '@/lib/api';
import type { Message, ResumeInfo, JobRequirements, WriterChatSessionInitRequest } from '@/types';

interface UseWriterChatProps {
  cvData: ResumeInfo | null;
  jobData: JobRequirements | null;
  flowMode?: 'cv_only' | 'job_tailoring' | null;
}

interface UseWriterChatReturn {
  // Session state
  sessionId: string | null;
  isInitializing: boolean;
  sessionError: string | null;
  
  // Chat state
  messages: Message[];
  fadingOutMessageId: string | null;
  inputText: string;
  setInputText: (text: string) => void;
  isLoading: boolean;
  chatError: string | null;
  
  // Refs
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  
  // Methods
  initializeSession: () => Promise<void>;
  handleSendMessage: () => Promise<void>;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  clearError: () => void;
  addMessage: (message: Message) => void;
  resetSession: () => void;
}

export const useWriterChat = ({ 
  cvData, 
  jobData,
  flowMode,
}: UseWriterChatProps): UseWriterChatReturn => {
  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [fadingOutMessageId, setFadingOutMessageId] = useState<string | null>(null);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  
  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputText]);

  const initializeSession = useCallback(async () => {
    if (sessionId) return; // Already initialized
    if (!cvData) return; // Need CV data to start

    setIsInitializing(true);
    setSessionError(null);

    try {
      // Determine mode: explicit flowMode takes precedence over jobData inference
      const mode: 'resume_refinement' | 'job_tailoring' = flowMode === 'cv_only'
        ? 'resume_refinement'
        : (jobData ? 'job_tailoring' : 'resume_refinement');

      const request: WriterChatSessionInitRequest = {
        cv_data: cvData,
        job_data: jobData || undefined,
        mode,
      };

      const response = await startWriterChat(request);
      
      if (response.success) {
        setSessionId(response.session_id);
        
        // Handle separate greeting and summary messages for smooth transition
        if (response.greeting_message && response.summary_message) {
          // First show greeting message
          const greetingMessage: Message = {
            id: `greeting-${Date.now()}`,
            role: 'assistant',
            content: response.greeting_message,
            timestamp: new Date(),
          };
          
          setMessages([greetingMessage]);
          
          // After 2.5 seconds, add summary message (keep greeting)
          setTimeout(() => {
            const summaryMessage: Message = {
              id: `summary-${Date.now()}`,
              role: 'assistant',
              content: response.summary_message!,
              timestamp: new Date(),
            };
            
            // Add summary message while keeping greeting
            setMessages((prev) => [...prev, summaryMessage]);
          }, 2500);
        } else {
          // Fallback to combined message if separate messages not available
          const initialMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: response.initial_message,
            timestamp: new Date(),
          };
          
          setMessages([initialMessage]);
        }
      } else {
        setSessionError('Failed to initialize Writer chat session');
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setSessionError(errorMessage);
      console.error('Writer chat initialization error:', err);
    } finally {
      setIsInitializing(false);
    }
  }, [sessionId, cvData, jobData, flowMode]);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const handleSendMessage = useCallback(async () => {
    if (!inputText.trim() || isLoading) return;
    
    if (!sessionId) {
      setChatError('Session not initialized. Please wait...');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setChatError(null);

    try {
      const response = await sendWriterMessage({
        session_id: sessionId,
        user_message: userMessage.content,
      });

      if (response.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.assistant_message,
          timestamp: new Date(),
          generatedFiles: response.generated_files,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Log if approval is required
        if (response.requires_approval) {
          console.log('Writer requires approval for next action');
        }

        // Log preview content if available
        if (response.preview_content) {
          console.log('Preview content:', response.preview_content);
        }
        
        // Log generated files if available
        if (response.generated_files && response.generated_files.length > 0) {
          console.log('Generated files:', response.generated_files);
        }
      } else {
        setChatError(response.message || 'Failed to send message');
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setChatError(errorMessage);
      
      // Add error message to chat
      const errorMessageObj: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessageObj]);
      
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, sessionId]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const clearError = useCallback(() => {
    setChatError(null);
    setSessionError(null);
  }, []);

  const resetSession = useCallback(() => {
    setSessionId(null);
    setMessages([]);
    setFadingOutMessageId(null);
    setSessionError(null);
    setChatError(null);
    setInputText('');
  }, []);

  return {
    // Session state
    sessionId,
    isInitializing,
    sessionError,
    
    // Chat state
    messages,
    fadingOutMessageId,
    inputText,
    setInputText,
    isLoading,
    chatError,
    
    // Refs
    textareaRef,
    messagesEndRef,
    
    // Methods
    initializeSession,
    handleSendMessage,
    handleKeyDown,
    clearError,
    addMessage,
    resetSession,
  };
};

