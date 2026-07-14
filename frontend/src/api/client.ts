import { clearSession, getAccessToken } from "../auth/session";
import type { AuthSession, ProjectListResponse, ProjectPayload, WebProject } from "../types";

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

export async function login(username: string, password: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
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

export function createProject(payload: ProjectPayload, accessToken?: string): Promise<WebProject> {
  return request<WebProject>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }, accessToken);
}

export function updateProject(id: string, payload: Partial<ProjectPayload>, accessToken?: string): Promise<WebProject> {
  return request<WebProject>(`/api/projects/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }, accessToken);
}

export function revealProjectCredential(id: string, accessToken?: string): Promise<{ project_id: string; password: string }> {
  return request<{ project_id: string; password: string }>(`/api/projects/${id}/credential`, undefined, accessToken);
}

export function deleteProject(id: string, accessToken?: string): Promise<void> {
  return request<void>(`/api/projects/${id}`, { method: "DELETE" }, accessToken);
}

