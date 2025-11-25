interface ChatInputProps {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputText: string;
  isLoading: boolean;
  onInputChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: () => void;
}

export const ChatInput = ({
  textareaRef,
  inputText,
  isLoading,
  onInputChange,
  onKeyDown,
  onSendMessage,
}: ChatInputProps) => {
  return (
    <div className="border-t border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-3">
          {/* Text Input */}
          <div className="flex-1">
            <div className="rounded-lg border border-slate-300 bg-white p-3 shadow-sm dark:border-slate-600 dark:bg-slate-700">
              <div className="mb-2 flex items-center gap-2">
                <svg className="h-4 w-4 text-slate-400 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Paste job description or URL here
                </span>
              </div>
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                className="w-full resize-none border-0 bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-0 dark:text-slate-100 dark:placeholder-slate-500"
                rows={1}
                style={{ minHeight: '24px', maxHeight: '200px' }}
              />
            </div>
          </div>
          
          {/* Send Button */}
          <button
            onClick={onSendMessage}
            disabled={!inputText.trim() || isLoading}
            className={`flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600 text-white shadow-md transition-all hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 dark:from-indigo-500 dark:to-blue-500 ${
              inputText.trim() && !isLoading ? 'hover:scale-105' : ''
            }`}
            aria-label="Send message"
          >
            {isLoading ? (
              <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Powered by AI. Your data is processed securely and privately.
        </p>
      </div>
    </div>
  );
};

