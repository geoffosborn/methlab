import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.METHLAB_API_BASE ?? "http://localhost:8020";

export async function GET(request: NextRequest) {
  const key = request.nextUrl.searchParams.get("key");
  if (!key) {
    return NextResponse.json({ error: "key parameter required" }, { status: 400 });
  }

  try {
    const apiUrl = new URL(`${API_BASE}/storage/presign`);
    apiUrl.searchParams.set("key", key);

    const res = await fetch(apiUrl.toString());
    if (!res.ok) throw new Error(`API ${res.status}`);

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to get presigned URL:", error);
    return NextResponse.json(
      { error: "Failed to get presigned URL" },
      { status: 502 }
    );
  }
}
