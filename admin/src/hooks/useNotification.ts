import { useCallback, useState } from "react";

export interface Notification {
  message: string;
  type: "success" | "error";
}

interface UseNotificationReturn {
  notification: Notification | null;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  dismiss: () => void;
}

export function useNotification(): UseNotificationReturn {
  const [notification, setNotification] = useState<Notification | null>(null);

  const showSuccess = useCallback((message: string) => {
    setNotification({ message, type: "success" });
    setTimeout(() => setNotification(null), 5000);
  }, []);

  const showError = useCallback((message: string) => {
    setNotification({ message, type: "error" });
    setTimeout(() => setNotification(null), 5000);
  }, []);

  const dismiss = useCallback(() => {
    setNotification(null);
  }, []);

  return { notification, showSuccess, showError, dismiss };
}
