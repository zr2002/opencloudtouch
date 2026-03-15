/**
 * Custom hook for device volume control.
 *
 * Syncs volume slider with backend device state.
 * Debounces volume changes to avoid flooding the device API.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import {
  getVolume,
  setVolume as setVolumeApi,
  setMute as setMuteApi,
  type VolumeState,
} from "../api/devices";

const POLL_INTERVAL_MS = 5000;
const DEBOUNCE_MS = 300;

export interface UseVolumeResult {
  volume: number;
  muted: boolean;
  loading: boolean;
  setDeviceVolume: (level: number) => void;
  toggleMute: () => void;
}

export function useVolume(deviceId: string | undefined): UseVolumeResult {
  const [volume, setVolume] = useState(0);
  const [muted, setMuted] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const pendingVolume = useRef(false);

  // Fetch volume from device
  const fetchVolume = useCallback(async () => {
    if (!deviceId || pendingVolume.current) return;
    try {
      const vol: VolumeState = await getVolume(deviceId);
      setVolume(vol.actual);
      setMuted(vol.muted);
    } catch (err) {
      console.warn("[useVolume] Failed to fetch volume:", err);
    }
  }, [deviceId]);

  // Initial fetch + polling
  useEffect(() => {
    if (!deviceId) return;

    setLoading(true);
    fetchVolume().finally(() => setLoading(false));

    const interval = setInterval(fetchVolume, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [deviceId, fetchVolume]);

  // Debounced volume setter — auto-unmutes when muted
  const setDeviceVolume = useCallback(
    (level: number) => {
      if (!deviceId) return;
      setVolume(level); // Optimistic update
      pendingVolume.current = true;

      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(async () => {
        try {
          const vol = await setVolumeApi(deviceId, level);
          setVolume(vol.actual);
          if (vol.muted) {
            // Auto-unmute when slider is moved while muted
            const unmuteVol = await setMuteApi(deviceId, false);
            setMuted(unmuteVol.muted);
            setVolume(unmuteVol.actual);
          } else {
            setMuted(vol.muted);
          }
        } catch (err) {
          console.error("[useVolume] Failed to set volume:", err);
        } finally {
          pendingVolume.current = false;
        }
      }, DEBOUNCE_MS);
    },
    [deviceId]
  );

  // Mute toggler
  const toggleMute = useCallback(() => {
    if (!deviceId) return;
    const newMuted = !muted;
    setMuted(newMuted); // Optimistic update
    setMuteApi(deviceId, newMuted)
      .then((vol) => {
        setMuted(vol.muted);
        setVolume(vol.actual);
      })
      .catch((err) => {
        console.error("[useVolume] Failed to toggle mute:", err);
        setMuted(!newMuted); // Rollback
      });
  }, [deviceId, muted]);

  return { volume, muted, loading, setDeviceVolume, toggleMute };
}
