import { Link } from 'react-router-dom';
import { useTheme } from '@/providers/ThemeProvider';
import { 
  SunIcon, 
  MoonIcon, 
  LightBulbIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  PuzzlePieceIcon,
} from '@heroicons/react/24/outline';

export default function Splash(): JSX.Element {
  const { theme, setTheme } = useTheme();

  const toggleTheme = (): void => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const getThemeIcon = (): JSX.Element => {
    if (theme === 'dark') {
      return <MoonIcon className="h-5 w-5" />;
    }
    return <SunIcon className="h-5 w-5" />;
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <LightBulbIcon className="h-8 w-8 text-primary" />
              <span className="text-2xl font-bold text-foreground">Promptly</span>
            </div>
            
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
              aria-label={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'} theme`}
            >
              {getThemeIcon()}
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6">
            Transform Your Ideas Into
            <span className="text-primary block">Perfect AI Prompts</span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Interactive prompting platform that guides you through iterative questioning 
            to craft and refine AI prompts for any large language model.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              to="/new"
              className="bg-primary text-primary-foreground px-8 py-3 rounded-lg font-semibold hover:bg-primary/90 transition-colors"
            >
              Create New Session
            </Link>
            <Link
              to="/app"
              className="border border-border px-8 py-3 rounded-lg font-semibold hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              Browse Sessions
            </Link>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="text-center">
              <div className="bg-accent rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <ChatBubbleLeftRightIcon className="h-8 w-8 text-accent-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Guided Iteration
              </h3>
              <p className="text-muted-foreground">
                AI-powered questions help refine your prompts step-by-step through intelligent dialogue.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-accent rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <PuzzlePieceIcon className="h-8 w-8 text-accent-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Visual Exploration
              </h3>
              <p className="text-muted-foreground">
                D3.js decision-tree visualizer shows your prompt's evolution and branching paths.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-accent rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <UserGroupIcon className="h-8 w-8 text-accent-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Collaborative
              </h3>
              <p className="text-muted-foreground">
                Share sessions, track versions, and work with teams to perfect your prompts.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-muted-foreground">
            <p>&copy; 2024 Promptly - Interactive AI Prompting Platform</p>
          </div>
        </div>
      </footer>
    </div>
  );
}