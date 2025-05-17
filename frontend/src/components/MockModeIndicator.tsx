import { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';

// This component will show a banner when the app is in mock data mode
const MockModeIndicator = () => {
  const [isMockMode, setIsMockMode] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Check if we're in mock mode by looking for console logs
    const originalConsoleLog = console.log;
    const originalConsoleWarn = console.warn;

    const checkForMockMode = (...args: any[]) => {
      if (
        typeof args[0] === 'string' && (
          args[0].includes('Using mock data') ||
          args[0].includes('switching to mock') ||
          args[0].includes('Backend unavailable')
        )
      ) {
        setIsMockMode(true);
      }
    };

    console.log = function(...args) {
      checkForMockMode(...args);
      originalConsoleLog.apply(console, args);
    };

    console.warn = function(...args) {
      checkForMockMode(...args);
      originalConsoleWarn.apply(console, args);
    };

    // Restore original console methods on cleanup
    return () => {
      console.log = originalConsoleLog;
      console.warn = originalConsoleWarn;
    };
  }, []);

  if (!isMockMode || !isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 max-w-md z-50 animate-in slide-in-from-right-10 duration-300">
      <div className="bg-amber-50 border border-amber-200 rounded-lg shadow-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-amber-800">Mock Data Mode</h3>
            <p className="text-sm text-amber-700 mt-1">
              The backend service is currently unavailable. The application is running with simulated data.
            </p>
            <div className="mt-3 flex justify-between items-center">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-amber-800 hover:text-amber-900 underline"
              >
                Check API Status
              </a>
              <button
                onClick={() => setIsVisible(false)}
                className="text-xs bg-amber-100 hover:bg-amber-200 text-amber-800 px-2 py-1 rounded"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MockModeIndicator;
