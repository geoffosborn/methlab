import type { PlumeAnnotated, PlumeListResponse, PlumeQueryParams } from "./types";

const API_BASE =
  process.env.CARBON_MAPPER_API_BASE ?? "https://api.carbonmapper.org/api/v1";

async function fetchApi<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  revalidate = 3600
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const res = await fetch(url.toString(), {
    next: { revalidate },
  });

  if (!res.ok) {
    throw new Error(`Carbon Mapper API error: ${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

export async function getPlumes(
  params: PlumeQueryParams = {}
): Promise<PlumeListResponse> {
  const { limit = 20, offset = 0, gas, sort, order, min_emission } = params;

  // The Carbon Mapper API doesn't support sort/order params,
  // so we fetch more data and sort client-side
  const fetchLimit = sort ? Math.max(limit + offset, 100) : limit;

  const queryParams: Record<string, string | number | undefined> = {
    limit: fetchLimit,
    offset: sort ? 0 : offset,
    gas,
  };

  const data = await fetchApi<PlumeListResponse>(
    "/catalog/plumes/annotated",
    queryParams
  );

  // Filter hidden and null emissions
  let items = data.items.filter((p) => !p.hide_emission);

  if (min_emission) {
    items = items.filter(
      (p) => p.emission_auto !== null && p.emission_auto >= min_emission
    );
  }

  // Client-side sorting
  if (sort === "emission_auto") {
    items.sort((a, b) => {
      const aVal = a.emission_auto ?? 0;
      const bVal = b.emission_auto ?? 0;
      return order === "asc" ? aVal - bVal : bVal - aVal;
    });
  } else if (sort === "published_at") {
    items.sort((a, b) => {
      const aDate = new Date(a.published_at).getTime();
      const bDate = new Date(b.published_at).getTime();
      return order === "asc" ? aDate - bDate : bDate - aDate;
    });
  }

  // Apply pagination after sorting
  if (sort) {
    items = items.slice(offset, offset + limit);
  }

  return {
    ...data,
    items,
  };
}

export async function getPlume(
  plumeId: string
): Promise<PlumeAnnotated | null> {
  try {
    const data = await fetchApi<PlumeListResponse>(
      "/catalog/plumes/annotated",
      { plume_id: plumeId, limit: 1 }
    );
    return data.items[0] ?? null;
  } catch {
    return null;
  }
}

export async function getTopEmitters(
  limit = 10
): Promise<PlumeAnnotated[]> {
  // Fetch a larger batch to find the top emitters
  const data = await fetchApi<PlumeListResponse>(
    "/catalog/plumes/annotated",
    { limit: Math.max(limit * 5, 100) },
    7200
  );

  return data.items
    .filter((p) => p.emission_auto !== null && !p.hide_emission)
    .sort((a, b) => (b.emission_auto ?? 0) - (a.emission_auto ?? 0))
    .slice(0, limit);
}

export async function getRecentPlumes(
  limit = 10
): Promise<PlumeAnnotated[]> {
  const data = await fetchApi<PlumeListResponse>(
    "/catalog/plumes/annotated",
    { limit: Math.max(limit * 3, 30) },
    1800
  );

  return data.items
    .filter((p) => !p.hide_emission)
    .sort(
      (a, b) =>
        new Date(b.published_at).getTime() -
        new Date(a.published_at).getTime()
    )
    .slice(0, limit);
}

export async function getPlumesByBbox(
  bbox: [number, number, number, number],
  limit = 100
): Promise<PlumeAnnotated[]> {
  const data = await fetchApi<PlumeListResponse>(
    "/catalog/plumes/annotated",
    {
      limit,
      plume_bounds: bbox.join(","),
    }
  );
  return data.items.filter((p) => !p.hide_emission);
}

export async function getPlumeCount(): Promise<number> {
  const data = await fetchApi<PlumeListResponse>(
    "/catalog/plumes/annotated",
    { limit: 1 },
    3600
  );
  return data.total_count;
}
