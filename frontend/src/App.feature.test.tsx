import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { encryptForPublicKey, getClientPublicKey } from "./utils/credentialTransport";

const project = {
  id: "project-1",
  name: "客户管理后台",
  url: "https://crm.example.com/login",
  category: "业务系统",
  description: "客户资料和销售流程",
  notes: "工作日使用",
  username: "crm-admin",
  password_masked: "********",
  has_credentials: true,
  has_screenshot: false,
  is_favorite: true,
  is_enabled: true,
  sort_order: 0,
  created_at: "2026-07-14T10:00:00Z",
  updated_at: "2026-07-14T10:00:00Z",
};

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function mockLoggedInProject(fetchMock: ReturnType<typeof vi.fn>, publicKey: string) {
  fetchMock
    .mockResolvedValueOnce(response({
      algorithm: "RSA-OAEP-SHA256",
      public_key: publicKey,
    }))
    .mockResolvedValueOnce(response({
      access_token: "test-token",
      token_type: "bearer",
      expires_in: 30 * 24 * 60 * 60,
      expires_at: Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60,
      user: { username: "admin", is_active: true },
    }))
    .mockResolvedValueOnce(response({ items: [project], total: 1 }));
}

function login() {
  fireEvent.change(screen.getByLabelText("管理员账号"), { target: { value: "admin" } });
  fireEvent.change(screen.getByLabelText("登录密码"), { target: { value: "admin@123" } });
  fireEvent.click(screen.getByRole("button", { name: "登录" }));
}

describe("glavk dashboard workflows", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders a project card and copies its password only after in-memory decryption", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const publicKey = await getClientPublicKey();
    const envelope = await encryptForPublicKey(publicKey, { username: "crm-admin", password: "crm-secret" });
    mockLoggedInProject(fetchMock, publicKey);
    fetchMock.mockResolvedValueOnce(response({ project_id: "project-1", envelope }));
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockResolvedValue(undefined) } });

    render(<App />);
    login();

    await waitFor(() => expect(screen.getByText("客户管理后台")).toBeInTheDocument());
    expect(screen.getByText("crm-admin")).toBeInTheDocument();
    expect(screen.getByText("********")).toBeInTheDocument();
    expect(screen.queryByText("crm-secret")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "复制密码" }));

    await waitFor(() => expect(screen.getByText("密码已复制")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenLastCalledWith("/api/projects/project-1/credential", expect.objectContaining({ headers: expect.any(Headers) }));
  });

  it("opens the add drawer, submits a project, and refreshes the list", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const publicKey = await getClientPublicKey();
    mockLoggedInProject(fetchMock, publicKey);
    fetchMock.mockResolvedValueOnce(response({ ...project, id: "project-2", name: "财务系统" }, 201));
    fetchMock.mockResolvedValueOnce(response({ items: [project, { ...project, id: "project-2", name: "财务系统" }], total: 2 }));

    render(<App />);
    login();
    await waitFor(() => expect(screen.getByText("客户管理后台")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "添加系统" }));
    expect(screen.getByRole("heading", { name: "添加网页系统" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("系统名称"), { target: { value: "财务系统" } });
    fireEvent.change(screen.getByLabelText("访问地址"), { target: { value: "https://finance.example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "保存系统" }));

    await waitFor(() => expect(screen.getByText("财务系统")).toBeInTheDocument());
    expect(screen.getByText("系统已保存")).toBeInTheDocument();
  });
});
