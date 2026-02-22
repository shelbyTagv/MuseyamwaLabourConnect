/**
 * WebSocket hook for real-time location & notification streams.
 */
import { useEffect, useRef, useCallback } from "react";

const WS_URL = (import.meta.env.VITE_API_URL || "").replace(/^http/, "ws");

export function useWebSocket(path, token, onMessage) {
    const wsRef = useRef(null);

    useEffect(() => {
        if (!token) return;
        const url = `${WS_URL}/api/v1${path}/${token}`;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => console.log(`[WS] Connected: ${path}`);
        ws.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                onMessage?.(data);
            } catch {
                // ignore
            }
        };
        ws.onerror = (e) => console.error(`[WS] Error:`, e);
        ws.onclose = () => console.log(`[WS] Disconnected: ${path}`);

        return () => ws.close();
    }, [path, token]);

    const send = useCallback((data) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);

    return { send, ws: wsRef };
}
