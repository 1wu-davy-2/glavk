import { clearSession, getAccessToken } from "../auth/session";
import type { AuthSession, CredentialEnvelope, CredentialPayload, ProjectListResponse, ProjectPayload, WebProject } from "../types";
import { decryptForClient, encryptForPublicKey, getClientPublicKey } from "../utils/credentialTransport";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

function notifyUnauthorized(): void {
  clearSession();
  window.dispatchEvent(new Event("auth-expired"));
}

function withAuth(init?: RequestInit, accessToken?: string): RequestInit {
  const headers = new Headers(init?.headers);
  const token = accessToken ?? getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return { ...init, headers };
}

async function request<T>(path: string, init?: RequestInit, accessToken?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, withAuth(init, accessToken));
  if (response.status === 401) {
    notifyUnauthorized();
    throw new Error("登录状态已过期，请重新登录");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `请求失败（${response.status}）`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function requestBlob(path: string, accessToken?: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, withAuth(undefined, accessToken));
  if (response.status === 401) {
    notifyUnauthorized();
    throw new Error("登录状态已过期，请重新登录");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `请求失败（${response.status}）`);
  }
  return response.blob();
}

async function getTransportPublicKey(): Promise<string> {
  const response = await fetch(`${API_BASE}/api/security/transport-key`, {
    headers: { "Cache-Control": "no-store" },
  });
  if (!response.ok) {
    throw new Error("暂时无法建立安全传输通道");
  }
  const body = await response.json() as { public_key?: unknown };
  if (typeof body.public_key !== "string" || !body.public_key) {
    throw new Error("暂时无法建立安全传输通道");
  }
  return body.public_key;
}

async function encryptProjectCredentials(
  username: string | undefined,
  password: string | undefined,
  isUpdate: boolean,
): Promise<CredentialEnvelope | undefined> {
  const normalizedUsername = username?.trim() ?? "";
  const normalizedPassword = password?.trim() ?? "";
  if (!normalizedUsername && !normalizedPassword) return undefined;
  const credentialPayload: CredentialPayload = {};
  if (!isUpdate || normalizedUsername || !normalizedPassword) credentialPayload.username = normalizedUsername;
  if (!isUpdate || normalizedPassword) credentialPayload.password = normalizedPassword || null;
  return encryptForPublicKey(await getTransportPublicKey(), credentialPayload);
}

async function projectBody(
  payload: ProjectPayload | Partial<ProjectPayload>,
  isUpdate: boolean,
): Promise<Record<string, unknown>> {
  const { username, password, ...rest } = payload;
  const credentialEnvelope = await encryptProjectCredentials(username, password, isUpdate);
  return credentialEnvelope ? { ...rest, credential_envelope: credentialEnvelope } : rest;
}

export async function login(username: string, password: string): Promise<AuthSession> {
  const credential_envelope = await encryptForPublicKey(
    await getTransportPublicKey(),
    { username: username.trim(), password },
  );
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential_envelope }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "用户名或密码错误");
  }
  const body = await response.json();
  return {
    accessToken: body.access_token,
    expiresAt: body.expires_at * 1000,
    user: body.user,
  };
}

export function listProjects(search = "", category = "", favorite = false, accessToken?: string): Promise<ProjectListResponse> {
  const params = new URLSearchParams();
  if (search.trim()) params.set("search", search.trim());
  if (category) params.set("category", category);
  if (favorite) params.set("favorite", "true");
  const query = params.toString();
  return request<ProjectListResponse>(`/api/projects${query ? `?${query}` : ""}`, undefined, accessToken);
}

export async function createProject(payload: ProjectPayload, accessToken?: string): Promise<WebProject> {
  return request<WebProject>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await projectBody(payload, false)),
  }, accessToken);
}

export async function updateProject(id: string, payload: Partial<ProjectPayload>, accessToken?: string): Promise<WebProject> {
  return request<WebProject>(`/api/projects/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(await projectBody(payload, true)),
  }, accessToken);
}

export async function revealProjectCredential(id: string, accessToken?: string): Promise<CredentialPayload> {
  const clientPublicKey = await getClientPublicKey();
  const result = await request<{ project_id: string; envelope: CredentialEnvelope }>(
    `/api/projects/${id}/credential`,
    { headers: { "X-Client-Public-Key": clientPublicKey } },
    accessToken,
  );
  return decryptForClient(result.envelope);
}

export function getProjectScreenshot(id: string, accessToken?: string): Promise<Blob> {
  return requestBlob(`/api/projects/${id}/screenshot`, accessToken);
}

export function deleteProject(id: string, accessToken?: string): Promise<void> {
  return request<void>(`/api/projects/${id}`, { method: "DELETE" }, accessToken);
}
