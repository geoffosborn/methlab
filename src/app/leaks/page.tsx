import type { Metadata } from "next";
import { getPlumes } from "@/lib/api/carbon-mapper";
import PlumeCard from "@/components/ui/PlumeCard";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Leak Archive",
  description:
    "Browse satellite-detected methane and CO2 plumes from around the world. Sorted by emission rate.",
};

interface LeaksPageProps {
  searchParams: Promise<{
    page?: string;
    gas?: string;
    sort?: string;
  }>;
}

export default async function LeaksPage({ searchParams }: LeaksPageProps) {
  const params = await searchParams;
  const page = Number(params.page) || 1;
  const gas = params.gas as "CH4" | "CO2" | undefined;
  const sort = params.sort || "emission_auto";
  const limit = 12;
  const offset = (page - 1) * limit;

  const data = await getPlumes({
    limit,
    offset,
    gas,
    sort,
    order: "desc",
  });

  const totalPages = Math.ceil(data.total_count / limit);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Leak Archive</h1>
        <p className="text-zinc-500">
          {data.total_count.toLocaleString()} satellite-detected emission plumes
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8">
        <FilterLink href="/leaks" active={!gas} label="All" />
        <FilterLink
          href="/leaks?gas=CH4"
          active={gas === "CH4"}
          label="Methane (CH4)"
        />
        <FilterLink
          href="/leaks?gas=CO2"
          active={gas === "CO2"}
          label="CO2"
        />
        <span className="text-zinc-700 self-center">|</span>
        <FilterLink
          href={`/leaks?${gas ? `gas=${gas}&` : ""}sort=emission_auto`}
          active={sort === "emission_auto"}
          label="Highest Emission"
        />
        <FilterLink
          href={`/leaks?${gas ? `gas=${gas}&` : ""}sort=published_at`}
          active={sort === "published_at"}
          label="Most Recent"
        />
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {data.items.map((plume) => (
          <PlumeCard key={plume.plume_id} plume={plume} />
        ))}
      </div>

      {data.items.length === 0 && (
        <div className="text-center py-20 text-zinc-500">
          No plumes found matching your filters.
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-12">
          {page > 1 && (
            <Link
              href={`/leaks?page=${page - 1}${gas ? `&gas=${gas}` : ""}${sort !== "emission_auto" ? `&sort=${sort}` : ""}`}
              className="px-4 py-2 rounded-lg border border-zinc-700 text-zinc-400 hover:bg-zinc-800"
            >
              Previous
            </Link>
          )}
          <span className="px-4 py-2 text-zinc-500">
            Page {page} of {totalPages}
          </span>
          {page < totalPages && (
            <Link
              href={`/leaks?page=${page + 1}${gas ? `&gas=${gas}` : ""}${sort !== "emission_auto" ? `&sort=${sort}` : ""}`}
              className="px-4 py-2 rounded-lg border border-zinc-700 text-zinc-400 hover:bg-zinc-800"
            >
              Next
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

function FilterLink({
  href,
  active,
  label,
}: {
  href: string;
  active: boolean;
  label: string;
}) {
  return (
    <Link
      href={href}
      className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
        active
          ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
          : "bg-zinc-900 text-zinc-500 border border-zinc-800 hover:text-zinc-300 hover:border-zinc-700"
      }`}
    >
      {label}
    </Link>
  );
}
