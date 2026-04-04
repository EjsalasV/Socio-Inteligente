import { NextRequest } from "next/server";

const DEFAULT_API_BASE =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://socio-inteligente-production.up.railway.app";

const API_BASE =
  process.env.API_BASE_INTERNAL ??
  process.env.NEXT_PUBLIC_API_BASE ??
  process.env.NEXT_PUBLIC_API_URL ??
  DEFAULT_API_BASE;

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function buildTargetUrl(path: string[], search: string): string {
  const base = stripTrailingSlash(API_BASE.trim());
  const cleanPath = path.map((p) => encodeURIComponent(p)).join("/");
  return `${base}/${cleanPath}${search}`;
}

function copyHeaders(req: NextRequest): Headers {
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");
  return headers;
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  const { path } = await context.params;
  const targetUrl = buildTargetUrl(path || [], request.nextUrl.search || "");
  const method = request.method.toUpperCase();
  const headers = copyHeaders(request);
  const body =
    method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(targetUrl, {
      method,
      headers,
      body,
      redirect: "manual",
      cache: "no-store",
    });
  } catch (error) {
    return Response.json(
      {
        detail: "No se pudo conectar desde Vercel al backend.",
        target: targetUrl,
        error: error instanceof Error ? error.message : "unknown_error",
      },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  if (process.env.NODE_ENV !== "production") {
    responseHeaders.set("x-proxy-target", targetUrl);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: Promise<{ path: string[] }> }): Promise<Response> {
  return proxy(request, context);
}
