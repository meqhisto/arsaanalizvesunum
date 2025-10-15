import { api, setTokens } from "./api";

export type AuthUser = {
  id: number;
  email: string;
  ad?: string;
  soyad?: string;
  [key: string]: unknown;
};

type LoginResponse = {
  success: boolean;
  message?: string;
  data?: {
    access_token: string;
    refresh_token: string;
    expires_in: number;
    token_type: string;
    user: AuthUser;
  };
};

export async function login(email: string, password: string, remember = false) {
  const res = await api.post<LoginResponse>("/v1/auth/login", {
    email,
    password,
    remember_me: remember,
  });
  if (res.data?.success && res.data.data) {
    const { access_token, refresh_token, expires_in } = res.data.data;
    const refreshExpires = remember ? 60 * 60 * 24 * 30 : 60 * 60 * 24 * 7;
    setTokens({ access: access_token, refresh: refresh_token }, { accessExpires: expires_in, refreshExpires });
    return res.data.data;
  }
  throw new Error(res.data?.message || "Login failed");
}

export async function getProfile() {
  const res = await api.get("/v1/users/profile");
  return (res.data?.data as AuthUser) || null;
}

export async function logout() {
  setTokens({ access: null, refresh: null });
}
