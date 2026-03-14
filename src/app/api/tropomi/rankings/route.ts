import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.METHLAB_API_BASE ?? "http://localhost:8020";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const apiUrl = new URL(`${API_BASE}/tropomi/rankings`);
  if (searchParams.get("aggregation_period"))
    apiUrl.searchParams.set(
      "aggregation_period",
      searchParams.get("aggregation_period")!
    );
  if (searchParams.get("limit"))
    apiUrl.searchParams.set("limit", searchParams.get("limit")!);

  try {
    const res = await fetch(apiUrl.toString(), {
      next: { revalidate: 300 },
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch TROPOMI rankings:", error);
    return NextResponse.json(
      { error: "Failed to fetch rankings" },
      { status: 502 }
    );
  }
}
