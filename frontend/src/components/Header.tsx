import { ThemeToggle } from './ThemeToggle';

interface HeaderProps {
  isDark: boolean;
  toggleTheme: () => void;
}

export const Header = ({ isDark, toggleTheme }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/80 backdrop-blur-md dark:border-slate-700/80 dark:bg-slate-900/80">
      <div className="relative flex h-16 w-full items-center">
        <div className="container mx-auto flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600 dark:from-indigo-500 dark:to-blue-500">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
              AIpply
            </h1>
          </div>
        </div>
        
        {/* Dark Mode Toggle - Positioned at absolute top-right */}
        <div className="absolute right-6 flex items-center gap-4">
          <ThemeToggle isDark={isDark} toggleTheme={toggleTheme} />
        </div>
      </div>
    </header>
  );
};


