import { beforeEach, describe, expect, it, vi } from "vitest";

import { copyText } from "./clipboard";

describe("copyText", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockRejectedValue(new Error("permission denied")) } });
  });

  it("falls back to the document copy command when clipboard permission is denied", async () => {
    Object.defineProperty(document, "execCommand", { configurable: true, value: vi.fn().mockReturnValue(true) });
    const execCommand = vi.spyOn(document, "execCommand").mockReturnValue(true);

    await expect(copyText("crm-secret")).resolves.toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
  });
});
