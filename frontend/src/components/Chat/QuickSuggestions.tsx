interface QuickSuggestionsProps {
  onSuggestionClick: (text: string) => void;
}

export const QuickSuggestions = ({ onSuggestionClick }: QuickSuggestionsProps) => {
  const suggestions = [
    { emoji: '💡', text: 'How can I improve my resume?' },
    { emoji: '🎯', text: 'Match my resume to a job description' },
    { emoji: '⭐', text: 'What skills should I highlight?' },
  ];

  return (
    <div className="mt-8 hidden grid-cols-1 gap-3 sm:grid sm:grid-cols-2 lg:grid-cols-3">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSuggestionClick(suggestion.text)}
          className="group rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm text-slate-700 transition-all hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300 dark:hover:border-indigo-600 dark:hover:bg-indigo-950/30 dark:hover:text-indigo-400"
        >
          <span className="font-medium">{suggestion.emoji}</span> {suggestion.text}
        </button>
      ))}
    </div>
  );
};


