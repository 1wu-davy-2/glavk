import { describe, expect, it } from "vitest";

import { decryptForClient, encryptForPublicKey, getClientPublicKey } from "./credentialTransport";

describe("credential transport", () => {
  it("encrypts credentials without sending plaintext and decrypts a client envelope", async () => {
    const clientPublicKey = await getClientPublicKey();
    const outgoing = await encryptForPublicKey(clientPublicKey, { username: "admin", password: "secret" });

    expect(JSON.stringify(outgoing)).not.toContain("admin");
    expect(JSON.stringify(outgoing)).not.toContain("secret");

    const incoming = await encryptForPublicKey(clientPublicKey, { username: "admin", password: "secret" });
    await expect(decryptForClient(incoming)).resolves.toEqual({ username: "admin", password: "secret" });
  });
});
