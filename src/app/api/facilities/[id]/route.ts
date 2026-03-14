import { NextRequest, NextResponse } from "next/server";
import { getFacility } from "@/lib/api/methlab-api";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const facilityId = Number(id);

  if (isNaN(facilityId)) {
    return NextResponse.json({ error: "Invalid facility ID" }, { status: 400 });
  }

  try {
    const facility = await getFacility(facilityId);
    if (!facility) {
      return NextResponse.json(
        { error: "Facility not found" },
        { status: 404 }
      );
    }
    return NextResponse.json(facility);
  } catch (error) {
    console.error("Failed to fetch facility:", error);
    return NextResponse.json(
      { error: "Failed to fetch facility data" },
      { status: 502 }
    );
  }
}
