import type {
  Facility,
  FacilityListResponse,
  FacilityQueryParams,
} from "./facility-types";

const API_BASE =
  process.env.METHLAB_API_BASE ?? "http://localhost:8020";

async function fetchApi<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  revalidate = 60,
  retries = 2
): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  let lastError: Error | null = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url.toString(), {
        next: { revalidate },
      });

      if (!res.ok) {
        throw new Error(`MethLab API error: ${res.status} ${res.statusText}`);
      }

      return res.json() as Promise<T>;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
      }
    }
  }

  throw lastError!;
}

export async function getFacilities(
  params: FacilityQueryParams = {}
): Promise<FacilityListResponse> {
  const { facility_type, state, status, limit = 200, offset = 0 } = params;

  return fetchApi<FacilityListResponse>("/facilities", {
    facility_type,
    state,
    status,
    limit,
    offset,
  });
}

export async function getFacility(id: number): Promise<Facility | null> {
  try {
    return await fetchApi<Facility>(`/facilities/${id}`);
  } catch {
    return null;
  }
}

export async function searchFacilitiesByBbox(
  bbox: string,
  limit = 200
): Promise<FacilityListResponse> {
  return fetchApi<FacilityListResponse>("/facilities/search", { bbox, limit });
}
