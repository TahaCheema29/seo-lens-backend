import { NextRequest, NextResponse } from "next/server";

function backendBase(): string {
  const url = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

/**
 * Proxies to FastAPI POST /billing/checkout.
 * Accepts optional body fields (ignored by backend except success_path / cancel_path).
 * Forwards Authorization and Cookie so the API can authenticate the user.
 */
export async function POST(req: NextRequest) {
  const auth = req.headers.get("authorization");
  const cookie = req.headers.get("cookie");

  let raw: Record<string, unknown> = {};
  try {
    raw = (await req.json()) as Record<string, unknown>;
  } catch {
    /* optional body */
  }

  const payload = {
    success_path:
      typeof raw.success_path === "string" ? raw.success_path : "/dashboard/subscription",
    cancel_path:
      typeof raw.cancel_path === "string" ? raw.cancel_path : "/dashboard/subscription",
  };

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) headers.Authorization = auth;
  if (cookie) headers.Cookie = cookie;

  const res = await fetch(`${backendBase()}/billing/checkout`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  const json = (await res.json().catch(() => ({}))) as {
    status?: string;
    message?: string;
    data?: { id?: string; url?: string };
  };

  const sessionId = json?.data?.id;
  const out = {
    ...json,
    result: { id: sessionId },
  };

  if (!res.ok) {
    return NextResponse.json(out, { status: res.status });
  }

  const ok = json?.status === "success" && !!sessionId;
  return NextResponse.json(out, { status: ok ? 200 : 400 });
}
