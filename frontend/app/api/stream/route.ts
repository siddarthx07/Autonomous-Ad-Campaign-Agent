import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
  const sessionId = req.nextUrl.searchParams.get("session_id");
  if (!sessionId) {
    return new Response("Missing session_id", { status: 400 });
  }

  const backendUrl = `${BACKEND_URL}/api/campaign/stream?session_id=${sessionId}`;

  const backendResponse = await fetch(backendUrl, {
    headers: { Accept: "text/event-stream" },
    // @ts-expect-error next fetch supports duplex
    duplex: "half",
  });

  if (!backendResponse.ok) {
    return new Response("Backend error", { status: backendResponse.status });
  }

  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
