import { NextRequest, NextResponse } from "next/server";

function backendBase(): string {
  const url = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

export async function GET(req: NextRequest) {
  const auth = req.headers.get("authorization");
  const cookie = req.headers.get("cookie");

  const headers: Record<string, string> = {};
  if (auth) headers.Authorization = auth;
  if (cookie) headers.Cookie = cookie;

  const res = await fetch(`${backendBase()}/billing/subscription`, {
    method: "GET",
    headers,
    cache: "no-store",
  });

  const json = await res.json().catch(() => ({}));
  return NextResponse.json(json, { status: res.status });
}
