"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WS_URL } from "@/lib/constants";
import type { Article, WSMessage } from "@/lib/types";

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];

interface UseWebSocketReturn {
  isConnected: boolean;
  lastArticle: Article | null;
  searchResults: Article[];
  sendSearch: (query: string) => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const [lastArticle, setLastArticle] = useState<Article | null>(null);
  const [searchResults, setSearchResults] = useState<Article[]>([]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_URL}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      retryRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        if (msg.type === "new_article" && msg.data && !Array.isArray(msg.data)) {
          setLastArticle(msg.data);
        }

        if (msg.type === "search_results" && Array.isArray(msg.data)) {
          setSearchResults(msg.data);
        }

        if (msg.type === "ping") {
          ws.send(JSON.stringify({ type: "pong" }));
        }
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      const delay =
        RECONNECT_DELAYS[Math.min(retryRef.current, RECONNECT_DELAYS.length - 1)];
      retryRef.current += 1;
      setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const sendSearch = useCallback((query: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "search", query }));
    }
  }, []);

  return { isConnected, lastArticle, searchResults, sendSearch };
}
