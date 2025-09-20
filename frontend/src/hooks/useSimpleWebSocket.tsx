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

// FIXED: Ultra-stable WebSocket hook that prevents infinite reconnections
export function useSimpleCoinWebSocket(
  coinId: string,
  enabled: boolean = true
) {
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use refs to avoid triggering useEffect dependencies
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const mountedRef = useRef(true);
  const isConnectingRef = useRef(false);

  const maxReconnectAttempts = 2; // Reduced attempts
  const reconnectDelay = 5000; // 5 second delay

  // Stable disconnect function
  const disconnect = useCallback(() => {
    console.log(`🔌 Disconnecting WebSocket for ${coinId}`);

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
    isConnectingRef.current = false;
  }, [coinId]);

  // Stable connect function with comprehensive checks
  const connect = useCallback(() => {
    if (!mountedRef.current || !enabled) {
      console.log(
        `❌ Not connecting - mounted: ${mountedRef.current}, enabled: ${enabled}`
      );
      return;
    }

    // Prevent multiple simultaneous connections
    if (
      isConnectingRef.current ||
      (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)
    ) {
      console.log(
        `⚠️ Connection already in progress or established for ${coinId}`
      );
      return;
    }

    // Check reconnection attempts
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      setError(`Max reconnection attempts exceeded (${maxReconnectAttempts})`);
      return;
    }

    isConnectingRef.current = true;

    try {
      console.log(
        `🔗 Connecting to WebSocket for ${coinId} (attempt ${
          reconnectAttemptsRef.current + 1
        })`
      );

      const ws = new WebSocket(`ws://localhost:8000/ws/${coinId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current || !enabled) {
          ws.close();
          return;
        }
        console.log(`✅ Connected to ${coinId} WebSocket`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        isConnectingRef.current = false;
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === "initial_data" && message.data) {
            const data = Array.isArray(message.data)
              ? message.data[0]
              : message.data;
            setPriceData(data);
          } else if (message.type === "price_update" && message.data) {
            const data = Array.isArray(message.data)
              ? message.data[0]
              : message.data;
            setPriceData(data);
          } else if (message.type === "error") {
            console.error(`WebSocket error for ${coinId}:`, message.error);
            setError(message.error || "Unknown WebSocket error");
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.onclose = (event) => {
        isConnectingRef.current = false;

        if (!mountedRef.current) return;

        console.log(
          `❌ WebSocket closed for ${coinId}: ${event.code} ${
            event.reason || "No reason"
          }`
        );
        setIsConnected(false);

        // Only auto-reconnect for unexpected closures and if still enabled
        if (
          event.code !== 1000 &&
          event.code !== 1001 &&
          reconnectAttemptsRef.current < maxReconnectAttempts &&
          enabled &&
          mountedRef.current
        ) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `🔄 Scheduling reconnection for ${coinId} in ${reconnectDelay}ms (attempt ${reconnectAttemptsRef.current})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current && enabled) {
              connect();
            }
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError(`Connection failed after ${maxReconnectAttempts} attempts`);
        }
      };

      ws.onerror = (err) => {
        isConnectingRef.current = false;
        if (!mountedRef.current) return;
        console.error(`WebSocket error for ${coinId}:`, err);
        setError("Connection error");
      };
    } catch (err) {
      isConnectingRef.current = false;
      console.error(`Failed to create WebSocket for ${coinId}:`, err);
      setError("Failed to create connection");
    }
  }, [coinId, enabled]);

  // Effect that only runs when coinId or enabled actually changes
  useEffect(() => {
    mountedRef.current = true;

    if (!enabled) {
      console.log(`🔴 WebSocket disabled for ${coinId}`);
      disconnect();
      return;
    }

    console.log(`🔵 WebSocket enabled for ${coinId}`);

    // Clean start
    disconnect();

    // Small delay to ensure clean disconnect before reconnecting
    const connectTimeout = setTimeout(() => {
      if (mountedRef.current && enabled) {
        connect();
      }
    }, 100);

    return () => {
      mountedRef.current = false;
      clearTimeout(connectTimeout);
      disconnect();
    };
  }, [coinId, enabled, connect, disconnect]);

  return {
    priceData,
    isConnected,
    error,
    reconnectAttempts: reconnectAttemptsRef.current,
  };
}

// Simple WebSocket status component
export function SimpleWebSocketStatus({
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
            (Retry {reconnectAttempts}/2)
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
