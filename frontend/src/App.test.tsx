import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("glavk application shell", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("logs in through the Chinese form and opens the dashboard", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              access_token: "test-token",
              token_type: "bearer",
              expires_in: 30 * 24 * 60 * 60,
              expires_at: Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60,
              user: { username: "admin", is_active: true },
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ items: [], total: 0 }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
    );

    render(<App />);
    fireEvent.change(screen.getByLabelText("管理员账号"), { target: { value: "admin" } });
    fireEvent.change(screen.getByLabelText("登录密码"), { target: { value: "admin@123" } });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    await waitFor(() => expect(screen.getByRole("heading", { name: "网页系统" })).toBeInTheDocument());
    expect(localStorage.getItem("glavk.session")).toContain("test-token");
    expect(screen.getByText("还没有网页系统")).toBeInTheDocument();
  });
});
