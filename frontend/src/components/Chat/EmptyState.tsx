import { QuickSuggestions } from './QuickSuggestions';

interface EmptyStateProps {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputText: string;
  isLoading: boolean;
  onInputChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSendMessage: () => void;
  onClickUpload: () => void;
}

export const EmptyState = ({
  textareaRef,
  inputText,
  isLoading,
  onInputChange,
  onKeyDown,
  onSendMessage,
  onClickUpload,
}: EmptyStateProps) => {
  return (
    <div className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="flex flex-1 flex-col items-center justify-start pt-16 sm:pt-20 md:pt-24 lg:pt-32">
        <div className="mx-auto w-full max-w-3xl px-6">
          {/* Question */}
          <div className="mb-10 text-center">
            <h2 className="mb-3 text-3xl font-semibold text-slate-900 dark:text-slate-100 sm:text-4xl">
              What would you like to work on today?
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 sm:text-base">
              Upload your resume and ask me anything to get started
            </p>
          </div>
          
          {/* Large Input Field */}
          <div className="w-full">
            <div className="relative flex items-center rounded-2xl border border-slate-300 bg-slate-50 px-4 py-4 shadow-sm transition-all focus-within:border-indigo-500 focus-within:bg-white focus-within:shadow-md dark:border-slate-600 dark:bg-slate-700/50 dark:focus-within:border-indigo-500 dark:focus-within:bg-slate-700">
              {/* Plus Icon */}
              <button
                onClick={onClickUpload}
                className="mr-3 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600 dark:text-slate-500 dark:hover:bg-slate-600 dark:hover:text-slate-300"
                aria-label="Add attachment"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
              
              {/* Text Input */}
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask any question"
                className="flex-1 resize-none border-0 bg-transparent text-base text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-0 dark:text-slate-100 dark:placeholder-slate-500"
                rows={1}
                style={{ minHeight: '32px', maxHeight: '200px' }}
              />
              
              {/* Right Side Icons */}
              <div className="ml-3 flex items-center gap-2">
                {/* Microphone Icon */}
                <button
                  className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600 dark:text-slate-500 dark:hover:bg-slate-600 dark:hover:text-slate-300"
                  aria-label="Voice input"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </button>
                
                {/* Send Button */}
                <button
                  onClick={onSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white transition-all hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600 ${
                    inputText.trim() && !isLoading ? 'hover:scale-105' : ''
                  }`}
                  aria-label="Send message"
                >
                  {isLoading ? (
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Quick Suggestions */}
          <QuickSuggestions onSuggestionClick={onInputChange} />
        </div>
      </div>
    </div>
  );
};

