"use client";
import { useCallback, useEffect, useRef, useState } from "react";

/** Only the current input revision owns a response, including errors and pending state. */
export function useReport<T>() {
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const revision = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const invalidate = useCallback(() => {
    revision.current += 1;
    controller.current?.abort();
    setResult(null); setError(null); setBusy(false);
  }, []);
  useEffect(() => () => { revision.current += 1; controller.current?.abort(); }, []);
  async function run(load: (signal: AbortSignal) => Promise<T>) {
    controller.current?.abort();
    const ownRevision = ++revision.current;
    const next = new AbortController(); controller.current = next;
    setBusy(true); setError(null); setResult(null);
    try {
      const data = await load(next.signal);
      if (revision.current === ownRevision) setResult(data);
    } catch (e) {
      if (revision.current === ownRevision && !next.signal.aborted) setError((e as Error).message);
    } finally {
      if (revision.current === ownRevision) setBusy(false);
    }
  }
  return { result, error, busy, invalidate, run };
}
