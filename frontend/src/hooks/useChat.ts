import { useState, useRef, useEffect } from 'react';
import { Message } from '@/types';

const getAgentIntroduction = (): string => {
  return `Hello! I'm your Resume AI Agent. I'm here to help you optimize your resume to perfectly match job descriptions.

Here's what I can do for you:
• Analyze your resume and identify areas for improvement
• Match your skills and experience to specific job requirements
• Suggest targeted improvements to make your resume stand out
• Help you tailor your resume for different positions

To get started, please upload your resume PDF and share a job description (either by pasting the text or providing a URL). I'll then analyze both and provide personalized recommendations to help you land that interview!

What would you like to work on today?`;
};

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Simulate API call delay
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAgentIntroduction(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return {
    messages,
    inputText,
    setInputText,
    isLoading,
    textareaRef,
    messagesEndRef,
    handleSendMessage,
    handleKeyDown,
  };
};


