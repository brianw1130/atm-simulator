import adminClient from "./client";
import type {
  AccountCreateData,
  AdminAccount,
  AdminAccountDetail,
  AdminCustomer,
  AdminCustomerDetail,
  AuditLogEntry,
  CustomerCreateData,
  CustomerUpdateData,
  MaintenanceStatus,
} from "./types";

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

// --- Customers ---

export async function getCustomers(): Promise<AdminCustomer[]> {
  const response = await adminClient.get<AdminCustomer[]>("/customers");
  return response.data;
}

export async function getCustomerDetail(
  customerId: number,
): Promise<AdminCustomerDetail> {
  const response = await adminClient.get<AdminCustomerDetail>(
    `/customers/${String(customerId)}`,
  );
  return response.data;
}

export async function createCustomer(
  data: CustomerCreateData,
): Promise<AdminCustomer> {
  const response = await adminClient.post<AdminCustomer>("/customers", data);
  return response.data;
}

export async function updateCustomer(
  customerId: number,
  data: CustomerUpdateData,
): Promise<AdminCustomer> {
  const response = await adminClient.put<AdminCustomer>(
    `/customers/${String(customerId)}`,
    data,
  );
  return response.data;
}

export async function deactivateCustomer(
  customerId: number,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/customers/${String(customerId)}/deactivate`,
  );
  return response.data;
}

export async function activateCustomer(
  customerId: number,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/customers/${String(customerId)}/activate`,
  );
  return response.data;
}

export async function createAccount(
  customerId: number,
  data: AccountCreateData,
): Promise<AdminAccountDetail> {
  const response = await adminClient.post<AdminAccountDetail>(
    `/customers/${String(customerId)}/accounts`,
    data,
  );
  return response.data;
}

export async function updateAccount(
  accountId: number,
  data: Record<string, number>,
): Promise<AdminAccountDetail> {
  const response = await adminClient.put<AdminAccountDetail>(
    `/accounts/${String(accountId)}`,
    data,
  );
  return response.data;
}

export async function closeAccount(
  accountId: number,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/accounts/${String(accountId)}/close`,
  );
  return response.data;
}

export async function resetPin(
  cardId: number,
  newPin: string,
): Promise<{ message: string }> {
  const response = await adminClient.post<{ message: string }>(
    `/cards/${String(cardId)}/reset-pin`,
    { new_pin: newPin },
  );
  return response.data;
}

// --- Data Export/Import ---

export async function exportSnapshot(): Promise<Blob> {
  const response = await adminClient.get<Blob>("/export", {
    responseType: "blob",
  });
  return response.data;
}

export async function importSnapshot(
  file: File,
  conflictStrategy: "skip" | "replace" = "skip",
): Promise<Record<string, number>> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await adminClient.post<Record<string, number>>(
    `/import?conflict_strategy=${conflictStrategy}`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return response.data;
}
