"use client";

import { useState } from "react";
import { getEmissionEquivalencies } from "@/lib/utils/formatting";

export default function CostCalculator() {
  const [emissionRate, setEmissionRate] = useState(100);
  const eq = getEmissionEquivalencies(emissionRate);

  // Estimated repair costs by sector (rough averages)
  const repairCostEstimate = emissionRate < 50 ? 15000 : emissionRate < 200 ? 50000 : 150000;
  const lostGasValuePerYear = emissionRate * 8760 * 0.5; // ~$0.50/kg natural gas

  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input */}
        <div>
          <label className="block text-sm text-zinc-500 uppercase tracking-wider mb-3">
            Emission Rate (kg/hr)
          </label>
          <input
            type="range"
            min={1}
            max={1000}
            value={emissionRate}
            onChange={(e) => setEmissionRate(Number(e.target.value))}
            className="w-full accent-orange-500"
          />
          <div className="flex justify-between text-xs text-zinc-600 mt-1">
            <span>1 kg/hr</span>
            <span className="text-2xl font-bold text-white">
              {emissionRate} kg/hr
            </span>
            <span>1,000 kg/hr</span>
          </div>
        </div>

        {/* Results */}
        <div className="space-y-4">
          <ResultRow
            label="Annual methane released"
            value={`${(eq.kgPerYear / 1000).toLocaleString(undefined, { maximumFractionDigits: 0 })} tonnes`}
          />
          <ResultRow
            label="CO2 equivalent per year"
            value={`${eq.co2eqTonnesPerYear.toLocaleString(undefined, { maximumFractionDigits: 0 })} tonnes`}
          />
          <ResultRow
            label="Equivalent cars on the road"
            value={eq.carsEquivalent.toLocaleString()}
          />
          <ResultRow
            label="Equivalent homes powered"
            value={eq.homesEquivalent.toLocaleString()}
          />
          <div className="border-t border-zinc-800 pt-4 space-y-3">
            <ResultRow
              label="Social cost of damage (EPA)"
              value={`$${eq.socialCostPerYear.toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr`}
              highlight="red"
            />
            <ResultRow
              label="Lost gas value"
              value={`$${lostGasValuePerYear.toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr`}
              highlight="red"
            />
            <ResultRow
              label="Estimated repair cost"
              value={`~$${repairCostEstimate.toLocaleString()}`}
              highlight="green"
            />
            <ResultRow
              label="Payback period"
              value={`${((repairCostEstimate / (eq.socialCostPerYear + lostGasValuePerYear)) * 12).toFixed(0)} months`}
              highlight="green"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ResultRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "red" | "green";
}) {
  const valueColor =
    highlight === "red"
      ? "text-red-400"
      : highlight === "green"
        ? "text-green-400"
        : "text-white";

  return (
    <div className="flex justify-between items-baseline">
      <span className="text-sm text-zinc-400">{label}</span>
      <span className={`font-mono font-bold ${valueColor}`}>{value}</span>
    </div>
  );
}
