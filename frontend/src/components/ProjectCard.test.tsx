import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectCard } from "./ProjectCard";

const baseProject = {
  id: "project-1",
  name: "客户管理后台",
  url: "https://crm.example.com",
  category: "业务系统",
  description: "",
  notes: "",
  username: "",
  password_masked: "",
  has_credentials: false,
  has_screenshot: false,
  is_favorite: false,
  is_enabled: true,
  sort_order: 0,
  created_at: "2026-07-14T10:00:00Z",
  updated_at: "2026-07-14T10:00:00Z",
};

const handlers = {
  onReveal: vi.fn(),
  onCopy: vi.fn(),
  onFavorite: vi.fn(),
  onEdit: vi.fn(),
  onDelete: vi.fn(),
};

describe("ProjectCard screenshot presentation", () => {
  it("shows the captured screenshot when a blob URL is available", () => {
    render(<ProjectCard project={{ ...baseProject, has_screenshot: true }} screenshotUrl="blob:project-1" {...handlers} />);

    expect(screen.getByRole("img", { name: "客户管理后台网页截图" })).toHaveAttribute("src", "blob:project-1");
  });

  it("keeps the initial avatar when no screenshot is available", () => {
    render(<ProjectCard project={baseProject} {...handlers} />);

    expect(screen.getByText("客")).toBeInTheDocument();
    expect(screen.queryByRole("img", { name: "客户管理后台网页截图" })).not.toBeInTheDocument();
  });
});
