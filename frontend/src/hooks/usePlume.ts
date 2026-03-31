"use client";

import useSWR from "swr";
import type { PlumeAnnotated } from "@/lib/api/types";

const fetcher = (url: string) =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error("Plume not found");
    return r.json();
  });

export function usePlume(id: string | null) {
  const { data, error, isLoading } = useSWR<PlumeAnnotated>(
    id ? `/api/plumes/${id}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 300000, // 5 minutes
    }
  );

  return {
    plume: data ?? null,
    error,
    isLoading,
  };
}
