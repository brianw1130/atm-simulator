import adminClient from "./client";
import type { AdminAccount, AuditLogEntry, MaintenanceStatus } from "./types";

// --- Auth ---

export async function login(
  username: string,
  password: string,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>("/login", {
    username,
    password,
  });
  return response.data;
}

export async function logout(): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>("/logout");
  return response.data;
}

// --- Accounts ---

export async function getAccounts(): Promise<AdminAccount[]> {
  const response = await adminClient.get<AdminAccount[]>("/accounts");
  return response.data;
}

export async function freezeAccount(
  accountId: number,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/accounts/${String(accountId)}/freeze`,
  );
  return response.data;
}

export async function unfreezeAccount(
  accountId: number,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/accounts/${String(accountId)}/unfreeze`,
  );
  return response.data;
}

// --- Audit Logs ---

export async function getAuditLogs(
  limit: number = 100,
  eventType?: string,
): Promise<AuditLogEntry[]> {
  const params: Record<string, string | number> = { limit };
  if (eventType) {
    params["event_type"] = eventType;
  }
  const response = await adminClient.get<AuditLogEntry[]>("/audit-logs", {
    params,
  });
  return response.data;
}

// --- Maintenance ---

export async function getMaintenanceStatus(): Promise<MaintenanceStatus> {
  const response =
    await adminClient.get<MaintenanceStatus>("/maintenance/status");
  return response.data;
}

export async function enableMaintenance(
  reason?: string,
): Promise<{ message: string }> {
  const body = reason ? { reason } : {};
  const response = await adminClient.post<{ message: string }>(
    "/maintenance/enable",
    body,
  );
  return response.data;
}

export async function disableMaintenance(): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    "/maintenance/disable",
  );
  return response.data;
}
