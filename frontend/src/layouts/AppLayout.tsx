import { useTheme } from '@/providers/ThemeProvider';
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';

export default function AppLayout(): JSX.Element {
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
      {/* Navigation Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-foreground">Promptly</h1>
              <span className="text-sm text-muted-foreground">
                Interactive AI Prompting Platform
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
                aria-label={`Switch to ${theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'} theme`}
              >
                {getThemeIcon()}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Welcome to Promptly
          </h2>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Your interactive AI prompting platform is ready! This is the main application layout 
            where authenticated users will craft and refine their AI prompts through guided iteration.
          </p>
          
          <div className="bg-card border border-border rounded-lg p-6 max-w-md mx-auto">
            <h3 className="text-lg font-semibold text-card-foreground mb-2">
              Next Steps
            </h3>
            <ul className="text-sm text-muted-foreground space-y-2 text-left">
              <li>• Implement authentication system</li>
              <li>• Add session management UI</li>
              <li>• Create prompt editor interface</li>
              <li>• Build D3.js decision tree visualizer</li>
              <li>• Add collaborative features</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
} 