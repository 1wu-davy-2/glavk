import type { CredentialEnvelope, CredentialPayload } from "../types";

export type { CredentialEnvelope, CredentialPayload } from "../types";

let clientKeyPair: CryptoKeyPair | null = null;

function bytesToBase64(bytes: ArrayBuffer | ArrayBufferView): string {
  const view = ArrayBuffer.isView(bytes)
    ? new Uint8Array(bytes.buffer as ArrayBuffer, bytes.byteOffset, bytes.byteLength)
    : new Uint8Array(bytes as ArrayBuffer);
  return btoa(String.fromCharCode(...view));
}

function base64ToBytes(value: string): ArrayBuffer {
  const decoded = atob(value);
  const bytes = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) bytes[index] = decoded.charCodeAt(index);
  return bytes.buffer;
}

async function getKeyPair(): Promise<CryptoKeyPair> {
  if (clientKeyPair) return clientKeyPair;
  clientKeyPair = await crypto.subtle.generateKey(
    { name: "RSA-OAEP", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    false,
    ["encrypt", "decrypt"],
  ) as CryptoKeyPair;
  return clientKeyPair;
}

export async function getClientPublicKey(): Promise<string> {
  const keyPair = await getKeyPair();
  const publicKey = await crypto.subtle.exportKey("spki", keyPair.publicKey);
  return bytesToBase64(publicKey);
}

async function importRsaPublicKey(publicKeyB64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("spki", base64ToBytes(publicKeyB64), { name: "RSA-OAEP", hash: "SHA-256" }, false, ["encrypt"]);
}

export async function encryptForPublicKey(publicKeyB64: string, payload: CredentialPayload): Promise<CredentialEnvelope> {
  const publicKey = await importRsaPublicKey(publicKeyB64);
  const aesKey = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode(JSON.stringify(payload));
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, aesKey, plaintext);
  const rawKey = await crypto.subtle.exportKey("raw", aesKey);
  const wrappedKey = await crypto.subtle.encrypt({ name: "RSA-OAEP" }, publicKey, rawKey);
  return { version: "v1", wrapped_key: bytesToBase64(wrappedKey), iv: bytesToBase64(iv), ciphertext: bytesToBase64(ciphertext) };
}

export async function decryptForClient(envelope: CredentialEnvelope): Promise<CredentialPayload> {
  const keyPair = await getKeyPair();
  const rawKey = await crypto.subtle.decrypt({ name: "RSA-OAEP" }, keyPair.privateKey, base64ToBytes(envelope.wrapped_key));
  const aesKey = await crypto.subtle.importKey("raw", rawKey, { name: "AES-GCM" }, false, ["decrypt"]);
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: base64ToBytes(envelope.iv) }, aesKey, base64ToBytes(envelope.ciphertext));
  return JSON.parse(new TextDecoder().decode(plaintext)) as CredentialPayload;
}

export function clearClientKey(): void {
  clientKeyPair = null;
}
