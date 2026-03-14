import type { Metadata } from "next";
import AlertsView from "@/components/monitoring/AlertsView";

export const metadata: Metadata = {
  title: "Alerts",
  description: "MethLab monitoring alerts — threshold exceedances, new detections, compliance.",
};

export default function AlertsPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Alerts</h1>
        <p className="text-zinc-500 mt-1">
          Methane emission alerts and compliance notifications
        </p>
      </div>

      <AlertsView />
    </div>
  );
}
