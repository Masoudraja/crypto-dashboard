"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";

interface PriceData {
  timestamp: string;
  price_usd: number;
  market_cap?: number;
  volume_24h?: number;
  change_24h?: number;
  sma_20?: number;
  ema_50?: number;
  rsi_14?: number;
  macd_line?: number;
  bb_upper?: number;
  bb_lower?: number;
}

interface WebSocketMessage {
  type: "initial_data" | "price_update" | "market_update" | "error";
  coin_id?: string;
  data?: PriceData | PriceData[];
  timestamp?: string;
  error?: string;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

// Custom hook for WebSocket connection
export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastConnectionAttempt, setLastConnectionAttempt] = useState(0);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
  } = options;

  const connect = useCallback(() => {
    const now = Date.now();

    // Throttle connection attempts to once per second
    if (now - lastConnectionAttempt < 1000) {
      console.log("Connection throttled - too frequent attempts");
      return;
    }

    // Prevent multiple simultaneous connection attempts
    if (isConnecting || ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Check if we've exceeded max reconnection attempts
    if (reconnectAttempts >= maxReconnectAttempts) {
      setError(`Max reconnection attempts (${maxReconnectAttempts}) exceeded`);
      return;
    }

    setLastConnectionAttempt(now);
    setIsConnecting(true);
    setError(null);

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        setReconnectAttempts(0);
        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        console.log(
          `WebSocket closed: Code ${event.code}, Reason: ${
            event.reason || "Unknown"
          }`
        );

        // Only auto-reconnect if:
        // 1. Auto-reconnect is enabled
        // 2. It wasn't a normal closure (code 1000)
        // 3. We haven't exceeded max attempts
        // 4. We're not already trying to reconnect
        if (
          autoReconnect &&
          event.code !== 1000 &&
          reconnectAttempts < maxReconnectAttempts &&
          !reconnectTimeoutRef.current
        ) {
          console.log(
            `Scheduling reconnection attempt ${
              reconnectAttempts + 1
            }/${maxReconnectAttempts} in ${reconnectInterval}ms`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setError(`Connection failed after ${maxReconnectAttempts} attempts`);
        }
      };

      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnecting(false);
        setError("WebSocket connection error");
        onError?.(error);
      };
    } catch (err) {
      setIsConnecting(false);
      setError("Failed to create WebSocket connection");
      console.error("WebSocket connection error:", err);
    }
  }, [
    url,
    onMessage,
    onError,
    onConnect,
    onDisconnect,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    isConnecting,
    reconnectAttempts,
    lastConnectionAttempt,
  ]);

  const disconnect = useCallback(() => {
    // Clear any pending reconnection attempts
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close the WebSocket connection
    if (ws.current) {
      ws.current.close(1000, "Manual disconnect"); // Normal closure
      ws.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setReconnectAttempts(0);
    setError(null);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected");
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    const initConnection = () => {
      if (mounted) {
        connect();
      }
    };

    initConnection();

    return () => {
      mounted = false;
      disconnect();
    };
  }, [url]); // Only depend on URL

  return {
    isConnected,
    lastMessage,
    error,
    reconnectAttempts,
    sendMessage,
    connect,
    disconnect,
  };
}

// Hook specifically for coin price updates
export function useCoinPriceWebSocket(coinId: string) {
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [priceHistory, setPriceHistory] = useState<PriceData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected, error, reconnectAttempts } = useWebSocket(
    `ws://localhost:8000/ws/${coinId}`,
    {
      onMessage: (message) => {
        if (message.type === "initial_data" && message.data) {
          const data = Array.isArray(message.data)
            ? message.data[0]
            : message.data;
          setPriceData(data);
          setPriceHistory([data]);
          setIsLoading(false);
        } else if (message.type === "price_update" && message.data) {
          const data = Array.isArray(message.data)
            ? message.data[0]
            : message.data;
          setPriceData(data);
          setPriceHistory((prev) => [...prev.slice(-99), data]); // Keep last 100 updates
        } else if (message.type === "error") {
          console.error(`WebSocket error for ${coinId}:`, message.error);
          setIsLoading(false);
        }
      },
      onConnect: () => {
        console.log(`Connected to ${coinId} price feed`);
        setIsLoading(true); // Reset loading when connecting
      },
      onDisconnect: () => {
        console.log(`Disconnected from ${coinId} price feed`);
      },
      onError: (error) => {
        console.error(`WebSocket error for ${coinId}:`, {
          type: error.type,
          target: error.target?.url,
          readyState: error.target?.readyState,
          error: error,
        });
        setIsLoading(false);
      },
      autoReconnect: true,
      reconnectInterval: 3000, // Reduced from 5000ms
      maxReconnectAttempts: 3, // Reduced from 5
    }
  );

  return {
    priceData,
    priceHistory,
    isLoading,
    isConnected,
    error,
    reconnectAttempts,
  };
}

// Hook for market overview updates
export function useMarketWebSocket() {
  const [marketData, setMarketData] = useState<PriceData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { isConnected, error, reconnectAttempts } = useWebSocket(
    "ws://localhost:8000/ws/market",
    {
      onMessage: (message) => {
        if (message.type === "market_update" && message.data) {
          const data = Array.isArray(message.data)
            ? message.data
            : [message.data];
          setMarketData(data);
          setIsLoading(false);
        }
      },
      onConnect: () => {
        console.log("Connected to market feed");
      },
      onDisconnect: () => {
        console.log("Disconnected from market feed");
      },
      onError: (error) => {
        console.error("Market WebSocket error:", error);
        setIsLoading(false);
      },
    }
  );

  return {
    marketData,
    isLoading,
    isConnected,
    error,
    reconnectAttempts,
  };
}

// Connection status component
export function WebSocketStatus({
  isConnected,
  error,
  reconnectAttempts,
}: {
  isConnected: boolean;
  error: string | null;
  reconnectAttempts: number;
}) {
  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 text-sm">
        <div className="h-2 w-2 bg-red-500 rounded-full"></div>
        Connection Error
        {reconnectAttempts > 0 && (
          <span className="text-xs text-gray-500">
            (Retry {reconnectAttempts}/5)
          </span>
        )}
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-yellow-600 text-sm">
        <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse"></div>
        Connecting...
        {reconnectAttempts > 0 && (
          <span className="text-xs text-gray-500">
            (Attempt {reconnectAttempts + 1}/5)
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-green-600 text-sm">
      <div className="h-2 w-2 bg-green-500 rounded-full"></div>
      Live
    </div>
  );
}
