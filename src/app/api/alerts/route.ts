import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.METHLAB_API_BASE ?? "http://localhost:8020";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const apiUrl = new URL(`${API_BASE}/alerts`);
  for (const [key, value] of searchParams.entries()) {
    apiUrl.searchParams.set(key, value);
  }

  try {
    const res = await fetch(apiUrl.toString(), { next: { revalidate: 30 } });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return NextResponse.json(await res.json());
  } catch (error) {
    console.error("Failed to fetch alerts:", error);
    return NextResponse.json(
      { error: "Failed to fetch alerts" },
      { status: 502 }
    );
  }
}
