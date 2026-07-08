import type { BackendNotification } from "../../types/backend"
import { unwrapBackendValue } from "./shared"

export function mapBackendNotificationToFrontendNotification(
  notification: BackendNotification
): {
  notificationId: number
  createdOn: string
  content: string
} {
  return {
    notificationId: unwrapBackendValue(notification.notification_id),
    createdOn: unwrapBackendValue(notification.created_on),
    content: unwrapBackendValue(notification.content),
  }
}
