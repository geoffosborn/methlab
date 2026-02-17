import { NextRequest, NextResponse } from "next/server";
import { getPlumes } from "@/lib/api/carbon-mapper";
import type { PlumeQueryParams } from "@/lib/api/types";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;

  const params: PlumeQueryParams = {
    limit: Number(searchParams.get("limit")) || 20,
    offset: Number(searchParams.get("offset")) || 0,
    gas: (searchParams.get("gas") as "CH4" | "CO2") || undefined,
    sort: searchParams.get("sort") || undefined,
    order: (searchParams.get("order") as "asc" | "desc") || undefined,
    min_emission: Number(searchParams.get("min_emission")) || undefined,
  };

  try {
    const data = await getPlumes(params);
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch plumes:", error);
    return NextResponse.json(
      { error: "Failed to fetch plume data" },
      { status: 502 }
    );
  }
}
