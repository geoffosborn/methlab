import { NextRequest, NextResponse } from "next/server";
import { getPlume } from "@/lib/api/carbon-mapper";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const plume = await getPlume(id);
    if (!plume) {
      return NextResponse.json({ error: "Plume not found" }, { status: 404 });
    }
    return NextResponse.json(plume);
  } catch (error) {
    console.error("Failed to fetch plume:", error);
    return NextResponse.json(
      { error: "Failed to fetch plume data" },
      { status: 502 }
    );
  }
}
