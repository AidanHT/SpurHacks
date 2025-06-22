import { Link } from 'react-router-dom';
import { useTheme } from '../providers/ThemeProvider';
import { MoonIcon, SunIcon } from '@heroicons/react/24/outline';

export default function HomePage() {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="relative px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <img 
              src="/logo.png" 
              alt="Promptly" 
              className="h-8 w-8 rounded-md"
            />
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              Promptly
            </span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            {theme === 'dark' ? (
              <SunIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            ) : (
              <MoonIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-6 py-12">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Section */}
          <div className="mb-12">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Transform Your Ideas Into
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                {' '}Perfect AI Prompts
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
              Craft and refine AI prompts through guided iteration and visual exploration. 
              Whether you're a beginner or expert, Promptly helps you create more effective prompts 
              through intelligent questioning and collaborative evolution.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/signup"
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 font-medium transition-colors shadow-lg"
              >
                Get Started Free
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-800 border border-blue-600 dark:border-blue-400 hover:bg-blue-50 dark:hover:bg-gray-700 font-medium transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>

          {/* Features Section */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="p-6 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
              <div className="w-12 h-12 mx-auto mb-4 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Guided Iteration
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                AI-powered questions help refine your prompts step-by-step through intelligent conversation.
              </p>
            </div>

            <div className="p-6 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
              <div className="w-12 h-12 mx-auto mb-4 bg-indigo-100 dark:bg-indigo-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Visual Exploration
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Interactive decision trees show your prompt's evolution and help you explore different paths.
              </p>
            </div>

            <div className="p-6 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
              <div className="w-12 h-12 mx-auto mb-4 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Multi-Model Support
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Target GPT-4, Claude, Llama, and other LLMs with prompts optimized for each model.
              </p>
            </div>
          </div>

          {/* Demo Section */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Ready to craft better prompts?
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Join thousands of users creating more effective AI prompts with Promptly.
            </p>
            <Link
              to="/signup"
              className="inline-flex items-center justify-center px-8 py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 font-medium transition-colors shadow-lg"
            >
              Start Your Free Account
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-600 dark:text-gray-300">
            © 2024 Promptly. Interactive AI Prompting Platform.
          </p>
        </div>
      </footer>
    </div>
  );
} 