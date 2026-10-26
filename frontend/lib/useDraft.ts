"use client";
import { useEffect, useState } from "react";

export function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function useDraft<T>(key: string, initial: T, valid: (value: unknown) => boolean) {
  const [value, setValue] = useState(initial);
  const [enabled, setEnabled] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        let parsed: unknown;
        try { parsed = JSON.parse(stored); }
        catch {
          localStorage.removeItem(key);
          setNotice("An unreadable saved draft was removed. Please re-enter your answers.");
          return;
        }
        if (valid(parsed)) { setValue(parsed as T); setEnabled(true); setNotice("Saved answers restored on this browser."); }
        else { localStorage.removeItem(key); setNotice("An incompatible saved draft was removed. Please re-enter your answers."); }
      }
    } catch { setNotice("Browser storage is unavailable or the saved draft cannot be read. Your form still works without saving."); }
  }, [key, valid]);
  useEffect(() => {
    if (!enabled) return;
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch { setNotice("Your latest changes could not be saved. Keep this page open or export your roadmap."); }
  }, [key, enabled, value]);
  function toggle(next: boolean) {
    try {
      if (next) localStorage.setItem(key, JSON.stringify(value));
      else localStorage.removeItem(key);
      setEnabled(next);
      setNotice(next ? "Draft saving is on for this browser only. Documents are never saved." : "Saved draft deleted. Current answers stay on this page until you leave.");
    } catch { setNotice("Browser storage could not be updated. Check your browser settings."); }
  }
  return { value, setValue, enabled, toggle, notice };
}
