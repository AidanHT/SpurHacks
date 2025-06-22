import { Routes, Route } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import ProtectedRoute from './routes/ProtectedRoute';

// Lazy load the app layout for better performance
const AppLayout = lazy(() => import('./layouts/AppLayout'));

function App() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        
        {/* Protected app routes */}
        <Route path="/app/*" element={
          <ProtectedRoute>
            <Suspense fallback={
              <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            }>
              <AppLayout />
            </Suspense>
          </ProtectedRoute>
        } />
        
        {/* Catch all route */}
        <Route path="*" element={
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-primary">404</h1>
              <p className="text-muted-foreground mt-2">Page not found</p>
            </div>
          </div>
        } />
      </Routes>
    </div>
  );
}

export default App; 