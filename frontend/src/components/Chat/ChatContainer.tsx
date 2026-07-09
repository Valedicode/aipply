import { Message, OrchestratorGateAction, OrchestratorGatePayload } from '@/types';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { ApprovalGate } from './ApprovalGate';
import { ChoiceGate } from './ChoiceGate';
import { InputGate } from './InputGate';

interface ChatContainerProps {
  messages: Message[];
  fadingOutMessageId?: string | null;
  inputText: string;
  isLoading: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onInputChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: () => void;
  onClickUpload: () => void;
  sessionReady?: boolean;
  // Orchestrator-only: when set, render the structured gate panel above the
  // free-text input. Legacy writer chat leaves these unset and the UI behaves
  // exactly as before.
  pendingGate?: OrchestratorGatePayload | null;
  onSubmitGateResolution?: (
    action: OrchestratorGateAction,
    opts?: { feedback?: string; choice?: string }
  ) => void | Promise<void>;
}

export const ChatContainer = ({
  messages,
  fadingOutMessageId,
  inputText,
  isLoading,
  textareaRef,
  messagesEndRef,
  onInputChange,
  onKeyDown,
  onSendMessage,
  onClickUpload,
  sessionReady = true,
  pendingGate,
  onSubmitGateResolution,
}: ChatContainerProps) => {
  if (messages.length === 0) {
    return (
      <EmptyState
        textareaRef={textareaRef}
        inputText={inputText}
        isLoading={isLoading}
        onInputChange={onInputChange}
        onKeyDown={onKeyDown}
        onSendMessage={onSendMessage}
        onClickUpload={onClickUpload}
      />
    );
  }

  return (
    <div className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800 animate-fade-in">
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl">
          <div className="space-y-4">
            {messages.map((message) => (
              <ChatMessage 
                key={message.id} 
                message={message}
                generatedFiles={message.generatedFiles}
                isFadingOut={fadingOutMessageId === message.id}
              />
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-blue-600 dark:from-indigo-500 dark:to-blue-500">
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="rounded-2xl bg-slate-100 px-4 py-3 dark:bg-slate-700">
                  <div className="flex gap-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 animate-bounce rounded-full bg-slate-400"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Structured gate panel (orchestrator mode only) */}
      {pendingGate && onSubmitGateResolution && (
        <div className="border-t border-slate-200 bg-slate-50 px-6 py-4 dark:border-slate-700 dark:bg-slate-900/40">
          {pendingGate.kind === 'choice' ? (
            <ChoiceGate
              gate={pendingGate}
              isLoading={isLoading}
              onSubmit={onSubmitGateResolution}
            />
          ) : pendingGate.kind === 'input' ? (
            <InputGate
              gate={pendingGate}
              isLoading={isLoading}
              onSubmit={onSubmitGateResolution}
            />
          ) : (
            <ApprovalGate
              gate={pendingGate}
              isLoading={isLoading}
              onSubmit={onSubmitGateResolution}
            />
          )}
        </div>
      )}

      {/* Input Area */}
      <ChatInput
        textareaRef={textareaRef}
        inputText={inputText}
        isLoading={isLoading || !sessionReady}
        onInputChange={onInputChange}
        onKeyDown={onKeyDown}
        onSendMessage={onSendMessage}
      />
    </div>
  );
};

