import axios from "axios";

// Base URL uses Next.js rewrite to proxy to Flask backend
// NEXT_PUBLIC_API_BASE_URL should usually be "/api" (rewritten to backend)
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

const ACCESS_COOKIE = "accessToken";
const REFRESH_COOKIE = "refreshToken";

// Simple token store for dev (access only). For production, prefer HttpOnly cookies via Route Handlers.
let accessTokenMemory: string | null = null;
let refreshTokenMemory: string | null = null;

type TokenOptions = {
  accessExpires?: number;
  refreshExpires?: number;
};

function setBrowserCookie(name: string, value: string, maxAge: number) {
  document.cookie = `${name}=${value}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
}

function deleteBrowserCookie(name: string) {
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

function readBrowserCookie(name: string) {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
}

export function setTokens(tokens: { access?: string | null; refresh?: string | null }, options: TokenOptions = {}) {
  const accessMaxAge = options.accessExpires ?? 3600;
  const refreshMaxAge = options.refreshExpires ?? 60 * 60 * 24 * 30;

  if (typeof window !== "undefined") {
    if (tokens.access !== undefined) {
      accessTokenMemory = tokens.access;
      if (tokens.access) {
        localStorage.setItem("accessToken", tokens.access);
        setBrowserCookie(ACCESS_COOKIE, tokens.access, accessMaxAge);
      } else {
        localStorage.removeItem("accessToken");
        deleteBrowserCookie(ACCESS_COOKIE);
      }
    }
    if (tokens.refresh !== undefined) {
      refreshTokenMemory = tokens.refresh;
      if (tokens.refresh) {
        localStorage.setItem("refreshToken", tokens.refresh);
        setBrowserCookie(REFRESH_COOKIE, tokens.refresh, refreshMaxAge);
      } else {
        localStorage.removeItem("refreshToken");
        deleteBrowserCookie(REFRESH_COOKIE);
      }
    }
  } else {
    if (tokens.access !== undefined) accessTokenMemory = tokens.access;
    if (tokens.refresh !== undefined) refreshTokenMemory = tokens.refresh;
  }
}

export function getTokens() {
  if (typeof window !== "undefined") {
    return {
      access: accessTokenMemory || localStorage.getItem("accessToken") || readBrowserCookie(ACCESS_COOKIE),
      refresh: refreshTokenMemory || localStorage.getItem("refreshToken") || readBrowserCookie(REFRESH_COOKIE),
    };
  }
  return { access: accessTokenMemory, refresh: refreshTokenMemory };
}

export const api = axios.create({
  baseURL,
  withCredentials: true,
});

// Request interceptor: attach Authorization if available
api.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) {
    config.headers = config.headers || {};
    config.headers["Authorization"] = `Bearer ${access}`;
  }
  return config;
});

let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

async function refreshAccessToken(): Promise<string> {
  const { refresh } = getTokens();
  if (!refresh) throw new Error("No refresh token");

  // Perform refresh with refresh token in Authorization header
  const res = await api.post(
    "/v1/auth/refresh",
    {},
    {
      headers: {
        Authorization: `Bearer ${refresh}`,
      },
    }
  );
  const responseData = res.data?.data;
  const newAccess = responseData?.access_token;
  if (!newAccess) throw new Error("No access token in refresh response");
  const accessExpires = responseData?.expires_in ?? 3600;
  setTokens({ access: newAccess }, { accessExpires });
  return newAccess;
}

// Response interceptor: try refresh on 401 once
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error?.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue requests while refreshing
        return new Promise((resolve, reject) => {
          pendingRequests.push((token: string) => {
            try {
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers["Authorization"] = `Bearer ${token}`;
              resolve(api(originalRequest));
            } catch (e) {
              reject(e);
            }
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const newToken = await refreshAccessToken();
        // Replay queued requests
        pendingRequests.forEach((cb) => cb(newToken));
        pendingRequests = [];
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshErr) {
        pendingRequests = [];
        setTokens({ access: null, refresh: null });
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export async function pingBackend() {
  try {
    const res = await api.get("/");
    return { ok: true, status: res.status };
  } catch (err: any) {
    return { ok: false, error: err?.message };
  }
}
