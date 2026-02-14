import type { Notification as NotificationType } from "../../hooks/useNotification";

interface NotificationProps {
  notification: NotificationType | null;
  onDismiss: () => void;
}

export function NotificationToast({ notification, onDismiss }: NotificationProps) {
  if (!notification) return null;

  return (
    <div
      className={`notification notification--${notification.type}`}
      role="alert"
    >
      <span className="notification__message">{notification.message}</span>
      <button
        className="notification__dismiss"
        onClick={onDismiss}
        aria-label="Dismiss"
      >
        &times;
      </button>
    </div>
  );
}
