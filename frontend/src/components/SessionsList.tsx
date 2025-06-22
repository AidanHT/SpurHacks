import { useGetSessionsQuery } from '../services/api';
import { Link } from 'react-router-dom';

export default function SessionsList() {
  const { data: sessions, isLoading, error } = useGetSessionsQuery();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
        <p className="text-red-600 dark:text-red-400 text-sm">
          Failed to load sessions. Please try again.
        </p>
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center p-8">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No sessions yet
        </h3>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          Create your first AI prompt crafting session to get started.
        </p>
        <Link
          to="/app/sessions/new"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Create Session
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Your Sessions
        </h3>
        <Link
          to="/app/sessions/new"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          New Session
        </Link>
      </div>

      <div className="grid gap-4">
        {sessions.map((session: any) => (
          <div
            key={session.id}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  {session.title || 'Untitled Session'}
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                  {session.starter_prompt}
                </p>
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                  <span>
                    Status: <span className="capitalize">{session.status}</span>
                  </span>
                  <span>
                    Created: {new Date(session.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <Link
                to={`/app/sessions/${session.id}`}
                className="ml-4 inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                View
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 