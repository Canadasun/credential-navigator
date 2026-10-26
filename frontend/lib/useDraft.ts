"use client";
import { useEffect, useState } from "react";
import type { MessageKey } from "./i18n";

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function useDraft<T>(key: string, initial: T, valid: (value: unknown) => boolean) {
  const [value, setValue] = useState(initial);
  const [enabled, setEnabled] = useState(false);
  const [notice, setNotice] = useState<MessageKey | null>(null);
  useEffect(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        let parsed: unknown;
        try { parsed = JSON.parse(stored); }
        catch {
          localStorage.removeItem(key);
          setNotice("draft.corrupt");
          return;
        }
        if (valid(parsed)) { setValue(parsed as T); setEnabled(true); setNotice("draft.restored"); }
        else { localStorage.removeItem(key); setNotice("draft.incompatible"); }
      }
    } catch { setNotice("draft.unavailable"); }
  }, [key, valid]);
  useEffect(() => {
    if (!enabled) return;
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch { setNotice("draft.saveFailed"); }
  }, [key, enabled, value]);
  function toggle(next: boolean) {
    try {
      if (next) localStorage.setItem(key, JSON.stringify(value));
      else localStorage.removeItem(key);
      setEnabled(next);
      setNotice(next ? "draft.on" : "draft.deleted");
    } catch { setNotice("draft.updateFailed"); }
  }
  return { value, setValue, enabled, toggle, notice };
}
