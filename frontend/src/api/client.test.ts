import { beforeEach, describe, expect, it, vi } from "vitest";

import { createProject, login, revealProjectCredential } from "./client";
import { encryptForPublicKey, getClientPublicKey } from "../utils/credentialTransport";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("API credential transport", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("encrypts login credentials before sending the request", async () => {
    const publicKey = await getClientPublicKey();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ algorithm: "RSA-OAEP-SHA256", public_key: publicKey }))
      .mockResolvedValueOnce(jsonResponse({
        access_token: "token",
        expires_at: 1_800_000_000,
        user: { username: "admin", is_active: true },
      }));
    vi.stubGlobal("fetch", fetchMock);

    await login("admin", "login-secret");

    const requestBody = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(requestBody).toHaveProperty("credential_envelope");
    expect(requestBody).not.toHaveProperty("username");
    expect(requestBody).not.toHaveProperty("password");
    expect(JSON.stringify(requestBody)).not.toContain("login-secret");
  });

  it("encrypts project credentials and decrypts reveal responses in memory", async () => {
    const publicKey = await getClientPublicKey();
    const revealEnvelope = await encryptForPublicKey(publicKey, { username: "crm-admin", password: "crm-secret" });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ algorithm: "RSA-OAEP-SHA256", public_key: publicKey }))
      .mockResolvedValueOnce(jsonResponse({ id: "project-1", has_credentials: true }))
      .mockResolvedValueOnce(jsonResponse({ project_id: "project-1", envelope: revealEnvelope }));
    vi.stubGlobal("fetch", fetchMock);

    await createProject({
      name: "客户管理后台",
      url: "https://crm.example.com",
      category: "业务系统",
      description: "",
      notes: "",
      username: "crm-admin",
      password: "crm-secret",
      is_favorite: false,
      is_enabled: true,
      sort_order: 0,
    }, "token");
    const createBody = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(createBody).toHaveProperty("credential_envelope");
    expect(createBody).not.toHaveProperty("username");
    expect(createBody).not.toHaveProperty("password");
    expect(JSON.stringify(createBody)).not.toContain("crm-secret");

    const credentials = await revealProjectCredential("project-1", "token");
    expect(credentials).toEqual({ username: "crm-admin", password: "crm-secret" });
    const revealInit = fetchMock.mock.calls[2][1] as RequestInit;
    expect(new Headers(revealInit.headers).get("X-Client-Public-Key")).toBe(publicKey);
  });
});
