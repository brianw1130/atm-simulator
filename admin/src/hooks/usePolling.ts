import { useCallback, useEffect, useRef, useState } from "react";

interface UsePollingReturn<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number = 30_000,
): UsePollingReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  const refresh = useCallback(async () => {
    try {
      const result = await fetchRef.current();
      setData(result);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Fetch failed";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial mount + interval setup
  useEffect(() => {
    void refresh();
    intervalRef.current = setInterval(() => void refresh(), intervalMs);
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refresh, intervalMs]);

  // Re-fetch when fetchFn identity changes (e.g. filter/limit dependencies)
  const prevFetchRef = useRef(fetchFn);
  useEffect(() => {
    if (prevFetchRef.current !== fetchFn) {
      prevFetchRef.current = fetchFn;
      void refresh();
    }
  }, [fetchFn, refresh]);

  return { data, error, isLoading, refresh };
}
