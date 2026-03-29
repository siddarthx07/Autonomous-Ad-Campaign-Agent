import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const resp = await fetch(`${BACKEND_URL}/api/sessions`);
    const data = await resp.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ sessions: [] });
  }
}
