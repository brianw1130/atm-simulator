import apiClient from "./client";
import type {
  LoginRequest,
  LoginResponse,
  SessionRefreshResponse,
  AccountListResponse,
  BalanceInquiryResponse,
  WithdrawalRequest,
  WithdrawalResponse,
  DepositRequest,
  DepositResponse,
  TransferRequest,
  TransferResponse,
  StatementRequest,
  StatementResponse,
  PinChangeRequest,
} from "./types";

// --- Auth ---

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/auth/login", data);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function refreshSession(): Promise<SessionRefreshResponse> {
  const response =
    await apiClient.post<SessionRefreshResponse>("/auth/session/refresh");
  return response.data;
}

export async function changePin(data: PinChangeRequest): Promise<void> {
  await apiClient.post("/auth/pin/change", data);
}

// --- Accounts ---

export async function listAccounts(): Promise<AccountListResponse> {
  const response = await apiClient.get<AccountListResponse>("/accounts/");
  return response.data;
}

export async function getBalance(
  accountId: number,
): Promise<BalanceInquiryResponse> {
  const response = await apiClient.get<BalanceInquiryResponse>(
    `/accounts/${String(accountId)}/balance`,
  );
  return response.data;
}

// --- Transactions ---

export async function withdraw(
  data: WithdrawalRequest,
): Promise<WithdrawalResponse> {
  const response = await apiClient.post<WithdrawalResponse>(
    "/transactions/withdraw",
    data,
  );
  return response.data;
}

export async function deposit(
  data: DepositRequest,
): Promise<DepositResponse> {
  const response = await apiClient.post<DepositResponse>(
    "/transactions/deposit",
    data,
  );
  return response.data;
}

export async function transfer(
  data: TransferRequest,
): Promise<TransferResponse> {
  const response = await apiClient.post<TransferResponse>(
    "/transactions/transfer",
    data,
  );
  return response.data;
}

// --- Statements ---

export async function generateStatement(
  data: StatementRequest,
): Promise<StatementResponse> {
  const response = await apiClient.post<StatementResponse>(
    "/statements/generate",
    data,
  );
  return response.data;
}
