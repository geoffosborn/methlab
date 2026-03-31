"use client";

import useSWR from "swr";
import type { PlumeListResponse, PlumeQueryParams } from "@/lib/api/types";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function usePlumes(params: PlumeQueryParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set("limit", String(params.limit));
  if (params.offset) searchParams.set("offset", String(params.offset));
  if (params.gas) searchParams.set("gas", params.gas);
  if (params.sort) searchParams.set("sort", params.sort);
  if (params.order) searchParams.set("order", params.order);
  if (params.min_emission)
    searchParams.set("min_emission", String(params.min_emission));

  const query = searchParams.toString();
  const url = `/api/plumes${query ? `?${query}` : ""}`;

  const { data, error, isLoading, mutate } = useSWR<PlumeListResponse>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    }
  );

  return {
    plumes: data?.items ?? [],
    totalCount: data?.total_count ?? 0,
    error,
    isLoading,
    mutate,
  };
}
