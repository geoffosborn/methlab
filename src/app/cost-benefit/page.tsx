import type { Metadata } from "next";
import { getTopEmitters } from "@/lib/api/carbon-mapper";
import { getPlumeCoordinates, getSectorLabel } from "@/lib/api/types";
import {
  formatEmissionRate,
  formatCoordinate,
  getEmissionEquivalencies,
} from "@/lib/utils/formatting";
import { getEmissionSeverityColor } from "@/lib/plume/plume-color";
import CostCalculator from "@/components/ui/CostCalculator";

export const metadata: Metadata = {
  title: "Cost-Benefit Analysis",
  description:
    "The economic case for fixing methane leaks. Compare repair costs vs. environmental damage and lost product value.",
};

export default async function CostBenefitPage() {
  const topEmitters = await getTopEmitters(10);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
      <div className="mb-12">
        <h1 className="text-4xl font-bold mb-4">Cost-Benefit Analysis</h1>
        <p className="text-lg text-zinc-400 max-w-2xl">
          Most methane leaks are economically fixable. The cost of repair is
          typically a fraction of the environmental damage and lost product
          value. Explore the numbers.
        </p>
      </div>

      {/* Interactive calculator */}
      <section className="mb-16">
        <h2 className="text-2xl font-bold mb-6">Emission Calculator</h2>
        <CostCalculator />
      </section>

      {/* Real examples from top emitters */}
      <section>
        <h2 className="text-2xl font-bold mb-6">
          Real-World Examples: Top Emitters
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500 text-left">
                <th className="pb-3 pr-4">Location</th>
                <th className="pb-3 pr-4">Sector</th>
                <th className="pb-3 pr-4 text-right">Emission</th>
                <th className="pb-3 pr-4 text-right">CO2eq/yr</th>
                <th className="pb-3 pr-4 text-right">Cars Equiv.</th>
                <th className="pb-3 text-right">Social Cost/yr</th>
              </tr>
            </thead>
            <tbody>
              {topEmitters.map((plume) => {
                const { latitude, longitude } = getPlumeCoordinates(plume);
                const eq = getEmissionEquivalencies(plume.emission_auto ?? 0);
                const severity = getEmissionSeverityColor(plume.emission_auto);

                return (
                  <tr
                    key={plume.plume_id}
                    className="border-b border-zinc-800/50 hover:bg-zinc-900/50"
                  >
                    <td className="py-3 pr-4">
                      <div className="text-zinc-300">
                        {formatCoordinate(latitude, "lat")},{" "}
                        {formatCoordinate(longitude, "lon")}
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-zinc-400">
                      {getSectorLabel(plume.sector)}
                    </td>
                    <td className="py-3 pr-4 text-right">
                      <span
                        className="font-mono font-bold"
                        style={{ color: severity }}
                      >
                        {formatEmissionRate(plume.emission_auto)}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-right font-mono text-zinc-300">
                      {eq.co2eqTonnesPerYear.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}
                      t
                    </td>
                    <td className="py-3 pr-4 text-right font-mono text-zinc-300">
                      {eq.carsEquivalent.toLocaleString()}
                    </td>
                    <td className="py-3 text-right font-mono text-red-400">
                      $
                      {eq.socialCostPerYear.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Key facts */}
      <section className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
        <FactCard
          stat="$51"
          label="Social Cost of Carbon"
          detail="Per tonne CO2 equivalent (US EPA estimate)"
        />
        <FactCard
          stat="28x"
          label="Methane Potency"
          detail="Methane's global warming potential vs CO2 over 100 years (IPCC AR5)"
        />
        <FactCard
          stat="80x"
          label="Short-Term Impact"
          detail="Methane's warming potential over 20 years - acting fast matters"
        />
      </section>
    </div>
  );
}

function FactCard({
  stat,
  label,
  detail,
}: {
  stat: string;
  label: string;
  detail: string;
}) {
  return (
    <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
      <div className="text-3xl font-bold text-orange-400">{stat}</div>
      <div className="text-white font-semibold mt-1">{label}</div>
      <div className="text-sm text-zinc-500 mt-1">{detail}</div>
    </div>
  );
}
