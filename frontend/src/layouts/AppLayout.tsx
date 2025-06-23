import { useState } from 'react';
import { Link, useNavigate, Routes, Route } from 'react-router-dom';
import SessionsList from '../components/SessionsList';
import SessionCreate from '../components/SessionCreate';
import SessionDetail from '../components/SessionDetail';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { logout } from '../slices/authSlice';
import { useTheme } from '../providers/ThemeProvider';
import { 
  MoonIcon, 
  SunIcon, 
  UserCircleIcon,
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  DocumentTextIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { profile } = useAppSelector((state) => state.auth);
  const { theme, setTheme } = useTheme();

  const handleLogout = () => {
    dispatch(logout());
    navigate('/');
  };

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
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
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-6 px-3">
          <div className="space-y-1">
            <Link
              to="/app"
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <HomeIcon className="mr-3 h-5 w-5" />
              Dashboard
            </Link>
            <Link
              to="/app/sessions"
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <DocumentTextIcon className="mr-3 h-5 w-5" />
              Sessions
            </Link>
            <Link
              to="/app/settings"
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Cog6ToothIcon className="mr-3 h-5 w-5" />
              Settings
            </Link>
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500"
                >
                  <Bars3Icon className="h-6 w-6" />
                </button>
                <h1 className="ml-2 text-xl font-semibold text-gray-900 dark:text-white lg:ml-0">
                  Dashboard
                </h1>
              </div>

              <div className="flex items-center space-x-4">
                {/* Theme Toggle */}
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-lg text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                >
                  {theme === 'dark' ? (
                    <SunIcon className="h-5 w-5" />
                  ) : (
                    <MoonIcon className="h-5 w-5" />
                  )}
                </button>

                {/* Profile Dropdown */}
                <div className="relative group">
                  <button className="flex items-center space-x-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                    <UserCircleIcon className="h-8 w-8" />
                    <span className="text-sm font-medium">
                      {profile?.email || 'User'}
                    </span>
                  </button>
                  
                  {/* Dropdown Menu */}
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                    <Link
                      to="/app/profile"
                      className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Your Profile
                    </Link>
                    <Link
                      to="/app/settings"
                      className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Settings
                    </Link>
                    <hr className="my-1 border-gray-200 dark:border-gray-600" />
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route index element={
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Welcome to Promptly!
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300 mb-6">
                    Your AI prompt crafting workspace is ready. Start creating better prompts with guided iteration and visual exploration.
                  </p>
                  
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Create New Session
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                        Start a new prompt crafting session with AI guidance.
                      </p>
                      <Link 
                        to="/app/sessions/new"
                        className="block w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-center"
                      >
                        New Session
                      </Link>
                    </div>

                    <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Recent Sessions
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                        Continue working on your recent prompt sessions.
                      </p>
                      <Link 
                        to="/app/sessions"
                        className="block w-full bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors text-center"
                      >
                        View Sessions
                      </Link>
                    </div>

                    <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Documentation
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
                        Learn how to craft better prompts with our guides.
                      </p>
                      <a 
                        href="https://docs.promptly.ai"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors text-center"
                      >
                        Learn More
                      </a>
                    </div>
                  </div>
                </div>
              } />
              <Route path="sessions" element={
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                    Sessions
                  </h2>
                  <SessionsList />
                </div>
              } />
              <Route path="sessions/new" element={<SessionCreate />} />
              <Route path="sessions/:sessionId" element={<SessionDetail />} />
              <Route path="settings" element={
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Settings
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300">
                    Application settings will be available here.
                  </p>
                </div>
              } />
              <Route path="profile" element={
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    Profile
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300">
                    User profile settings will be available here.
                  </p>
                </div>
              } />
            </Routes>
          </div>
        </main>
      </div>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
} 