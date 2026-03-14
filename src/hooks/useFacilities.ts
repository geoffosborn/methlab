"use client";

import useSWR from "swr";
import type {
  FacilityListResponse,
  FacilityQueryParams,
} from "@/lib/api/facility-types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function useFacilities(params: FacilityQueryParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.facility_type)
    searchParams.set("facility_type", params.facility_type);
  if (params.state) searchParams.set("state", params.state);
  if (params.status) searchParams.set("status", params.status);
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.offset) searchParams.set("offset", String(params.offset));

  const query = searchParams.toString();
  const url = `/api/facilities${query ? `?${query}` : ""}`;

  const { data, error, isLoading, mutate } = useSWR<FacilityListResponse>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    facilities: data?.items ?? [],
    totalCount: data?.total_count ?? 0,
    error,
    isLoading,
    mutate,
  };
}
