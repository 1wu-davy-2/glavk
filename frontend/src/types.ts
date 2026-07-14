export interface AuthUser {
  username: string;
  is_active: boolean;
}

export interface AuthSession {
  accessToken: string;
  expiresAt: number;
  user: AuthUser;
}

export interface WebProject {
  id: string;
  name: string;
  url: string;
  category: string;
  description: string;
  notes: string;
  username: string;
  password_masked: string;
  is_favorite: boolean;
  is_enabled: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectPayload {
  name: string;
  url: string;
  category: string;
  description: string;
  notes: string;
  username: string;
  password?: string;
  is_favorite: boolean;
  is_enabled: boolean;
  sort_order: number;
}

export interface ProjectListResponse {
  items: WebProject[];
  total: number;
}

