/**
 * Geolocation hook with battery optimization.
 */
import { useState, useEffect, useCallback } from "react";

export function useGeolocation(enabled = false, intervalMs = 15000) {
    const [position, setPosition] = useState(null);
    const [error, setError] = useState(null);

    const updatePosition = useCallback(() => {
        if (!navigator.geolocation) {
            setError("Geolocation not supported");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) =>
                setPosition({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy,
                }),
            (err) => setError(err.message),
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
        );
    }, []);

    useEffect(() => {
        if (!enabled) return;
        updatePosition();
        const id = setInterval(updatePosition, intervalMs);
        return () => clearInterval(id);
    }, [enabled, intervalMs, updatePosition]);

    return { position, error };
}
