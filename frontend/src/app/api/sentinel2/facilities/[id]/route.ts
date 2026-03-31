import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.METHLAB_API_BASE ?? "http://localhost:8020";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = request.nextUrl;

  const apiUrl = new URL(`${API_BASE}/sentinel2/facilities/${id}`);
  if (searchParams.get("confidence"))
    apiUrl.searchParams.set("confidence", searchParams.get("confidence")!);
  if (searchParams.get("limit"))
    apiUrl.searchParams.set("limit", searchParams.get("limit")!);

  try {
    const res = await fetch(apiUrl.toString(), { next: { revalidate: 60 } });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch S2 detections:", error);
    return NextResponse.json(
      { error: "Failed to fetch S2 detection data" },
      { status: 502 }
    );
  }
}
