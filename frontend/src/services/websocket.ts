import { useEffect, useRef, useState, useCallback } from 'react';

// WebSocket service for real-time updates
export const useWebSocket = (clientId: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Send ping to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      wsRef.current = ws;
      
      // Clear interval on close
      ws.onclose = () => {
        clearInterval(pingInterval);
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after a delay
        setTimeout(() => {
          connect();
        }, 3000);
      };
    };
    
    // Handle incoming messages
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setMessages((prev) => [...prev, message]);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    // Handle errors
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      ws.close();
    };
    
    wsRef.current = ws;
  }, [clientId]);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);
  
  // Send message to WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }, []);
  
  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  return {
    isConnected,
    messages,
    sendMessage,
    connect,
    disconnect,
  };
};

export default useWebSocket;
