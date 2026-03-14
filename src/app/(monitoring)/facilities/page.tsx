import type { Metadata } from "next";
import { getFacilities } from "@/lib/api/methlab-api";
import type { Facility } from "@/lib/api/facility-types";
import FacilityExplorer from "@/components/monitoring/FacilityExplorer";

export const metadata: Metadata = {
  title: "Facilities",
  description:
    "Browse monitored Australian coal mine facilities with satellite methane monitoring.",
};

interface FacilitiesPageProps {
  searchParams: Promise<{
    state?: string;
    status?: string;
  }>;
}

export default async function FacilitiesPage({
  searchParams,
}: FacilitiesPageProps) {
  const params = await searchParams;

  let facilities: Facility[] = [];
  try {
    const data = await getFacilities({
      facility_type: "coal_mine",
      state: params.state,
      status: params.status,
      limit: 500,
    });
    facilities = data.items;
  } catch {
    // API not available yet — show empty state
    facilities = [];
  }

  return <FacilityExplorer facilities={facilities} />;
}
