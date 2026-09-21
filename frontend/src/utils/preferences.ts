const DISPLAY_NAME_KEY = "glavk.displayName";

export function loadDisplayName(): string {
  return localStorage.getItem(DISPLAY_NAME_KEY) ?? "";
}

export function saveDisplayName(value: string): void {
  if (value) localStorage.setItem(DISPLAY_NAME_KEY, value);
  else localStorage.removeItem(DISPLAY_NAME_KEY);
}
