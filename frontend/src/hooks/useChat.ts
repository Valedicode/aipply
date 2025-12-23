/**
 * Hook for managing chat interactions with the supervisor agent
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { sendSupervisorMessage, getErrorMessage } from '@/lib/api';
import type { Message, ResumeInfo } from '@/types';

interface UseChatProps {
  sessionId: string | null;
  cvData: ResumeInfo | null;
  onSessionStateUpdate?: (state: any) => void;
}

interface UseChatReturn {
  messages: Message[];
  inputText: string;
  setInputText: (text: string) => void;
  isLoading: boolean;
  error: string | null;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  handleSendMessage: () => Promise<void>;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  clearError: () => void;
  addMessage: (message: Message) => void;
}

export const useChat = ({ 
  sessionId, 
  cvData, 
  onSessionStateUpdate 
}: UseChatProps): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const handleSendMessage = useCallback(async () => {
    if (!inputText.trim() || isLoading) return;
    
    if (!sessionId) {
      setError('Session not initialized. Please wait...');
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
    setError(null);

    try {
      // Send message to supervisor agent
      const response = await sendSupervisorMessage({
        session_id: sessionId,
        user_input: userMessage.content,
      });

      if (response.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.assistant_message,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Update session state if callback provided
        if (response.session_state && onSessionStateUpdate) {
          onSessionStateUpdate(response.session_state);
        }

        // Handle next action suggestions
        if (response.next_action) {
          console.log('Next action suggested:', response.next_action);
        }
      } else {
        setError(response.message || 'Failed to send message');
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      
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
  }, [inputText, isLoading, sessionId, onSessionStateUpdate]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    inputText,
    setInputText,
    isLoading,
    error,
    textareaRef,
    messagesEndRef,
    handleSendMessage,
    handleKeyDown,
    clearError,
    addMessage,
  };
};
