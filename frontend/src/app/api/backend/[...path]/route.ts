import { NextRequest, NextResponse } from "next/server";

const backendBase = process.env.API_PROXY_TARGET || "http://localhost:5000";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD";
type RouteParams = { path?: string[] } | Promise<{ path: string[] }>;

async function resolveParams(params: RouteParams): Promise<{ path?: string[] }> {
  const candidate = params as Promise<{ path: string[] }>;
  if (candidate && typeof candidate.then === "function") {
    return candidate;
  }
  return params as { path?: string[] };
}

async function proxyRequest(method: HttpMethod, request: NextRequest, params: RouteParams) {
  const resolvedParams = await resolveParams(params);
  const relativePath = resolvedParams.path?.join("/") ?? "";
  const targetUrl = `${backendBase}/api/${relativePath}`;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const accessToken = request.cookies.get("accessToken")?.value;
  const refreshToken = request.cookies.get("refreshToken")?.value;

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let body: BodyInit | undefined;
  if (method !== "GET" && method !== "HEAD") {
    const contentType = request.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const json = await request.json();
      body = JSON.stringify(json);
    } else {
      body = await request.text();
    }
  }

  let backendResponse = await fetch(targetUrl, {
    method,
    headers,
    body,
  });

  let newAccessToken: string | null = null;
  let accessExpires = 3600;

  if (backendResponse.status === 401 && refreshToken) {
    const refreshResponse = await fetch(`${backendBase}/api/v1/auth/refresh`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (refreshResponse.ok) {
      try {
        const refreshData = await refreshResponse.json();
        newAccessToken = refreshData?.data?.access_token ?? null;
        accessExpires = refreshData?.data?.expires_in ?? 3600;
      } catch (error) {
        newAccessToken = null;
      }

      if (newAccessToken) {
        headers.set("Authorization", `Bearer ${newAccessToken}`);
        backendResponse = await fetch(targetUrl, {
          method,
          headers,
          body,
        });
      }
    } else {
      return buildResponse(refreshResponse);
    }
  }

  const finalResponse = await buildResponse(backendResponse);

  if (newAccessToken) {
    finalResponse.cookies.set("accessToken", newAccessToken, {
      path: "/",
      maxAge: accessExpires,
      sameSite: "lax",
    });
  }

  return finalResponse;
}

async function buildResponse(res: Response) {
  const contentType = res.headers.get("content-type") || "";
  const headers = new Headers(res.headers);
  if (contentType.includes("application/json")) {
    const data = await res.json();
    const response = NextResponse.json(data, { status: res.status });
    headers.forEach((value, key) => {
      if (!response.headers.has(key)) {
        response.headers.set(key, value);
      }
    });
    return response;
  }

  const arrayBuffer = await res.arrayBuffer();
  return new NextResponse(arrayBuffer, {
    status: res.status,
    headers,
  });
}

export async function GET(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("GET", request, context.params);
}

export async function POST(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("POST", request, context.params);
}

export async function PUT(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("PUT", request, context.params);
}

export async function PATCH(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("PATCH", request, context.params);
}

export async function DELETE(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("DELETE", request, context.params);
}

export async function OPTIONS(request: NextRequest, context: { params: RouteParams }) {
  return proxyRequest("OPTIONS", request, context.params);
}
