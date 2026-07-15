import { useCallback, useEffect, useRef, useState } from "react";

/** Laedt Daten sofort und danach in einem festen Intervall. */
export function usePolling<T>(
  loader: () => Promise<T>,
  intervalMs: number,
): { data: T | null; error: string | null; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback(() => {
    loaderRef
      .current()
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    reload();
    const timer = setInterval(reload, intervalMs);
    return () => clearInterval(timer);
  }, [reload, intervalMs]);

  return { data, error, reload };
}
