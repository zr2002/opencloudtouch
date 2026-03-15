/**
 * useZoneNames Hook (STORY-1009)
 * Manages user-defined zone names via localStorage.
 * Bose API has no zone name concept — names are purely client-side.
 */

import { useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "zone-names";
const MAX_NAME_LENGTH = 30;

export interface UseZoneNamesResult {
  getZoneName: (masterId: string, defaultName: string) => string;
  setZoneName: (masterId: string, name: string) => void;
  removeZoneName: (masterId: string) => void;
}

function loadNames(): Record<string, string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveNames(names: Record<string, string>): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(names));
}

export function useZoneNames(): UseZoneNamesResult {
  const [names, setNames] = useState<Record<string, string>>(loadNames);

  // Sync to localStorage on change
  useEffect(() => {
    saveNames(names);
  }, [names]);

  const getZoneName = useCallback(
    (masterId: string, defaultName: string): string => {
      return names[masterId] || defaultName;
    },
    [names]
  );

  const setZoneName = useCallback((masterId: string, name: string): void => {
    const trimmed = name.slice(0, MAX_NAME_LENGTH).trim();
    setNames((prev) => {
      if (!trimmed) {
        // Empty name → remove custom name, fallback to default
        const { [masterId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [masterId]: trimmed };
    });
  }, []);

  const removeZoneName = useCallback((masterId: string): void => {
    setNames((prev) => {
      const { [masterId]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  return { getZoneName, setZoneName, removeZoneName };
}
