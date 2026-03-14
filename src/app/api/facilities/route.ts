import { NextRequest, NextResponse } from "next/server";
import { getFacilities, searchFacilitiesByBbox } from "@/lib/api/methlab-api";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  try {
    // If bbox is provided, use spatial search
    const bbox = searchParams.get("bbox");
    if (bbox) {
      const data = await searchFacilitiesByBbox(
        bbox,
        Number(searchParams.get("limit")) || 200
      );
      return NextResponse.json(data);
    }

    // Otherwise, list with filters
    const data = await getFacilities({
      facility_type: searchParams.get("facility_type") || undefined,
      state: searchParams.get("state") || undefined,
      status: searchParams.get("status") || undefined,
      limit: Number(searchParams.get("limit")) || 200,
      offset: Number(searchParams.get("offset")) || 0,
    });
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch facilities:", error);
    return NextResponse.json(
      { error: "Failed to fetch facility data" },
      { status: 502 }
    );
  }
}
