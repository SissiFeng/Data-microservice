import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import MockModeIndicator from './components/MockModeIndicator';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // Reduce retries to quickly fall back to mock data
      retryDelay: 1000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
      <MockModeIndicator />
    </QueryClientProvider>
  );
}

export default App;
