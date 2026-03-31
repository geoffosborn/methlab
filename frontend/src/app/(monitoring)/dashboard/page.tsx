import type { Metadata } from "next";
import DashboardView from "@/components/monitoring/DashboardView";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "MethLab monitoring dashboard — facility rankings, recent detections, alerts.",
};

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Monitoring Dashboard</h1>
        <p className="text-zinc-500 mt-1">
          Australian coal mine methane monitoring overview
        </p>
      </div>

      <DashboardView />
    </div>
  );
}
