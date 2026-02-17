import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description:
    "How MethLab works: satellite detection, 3D visualization, and the mission to make fugitive emissions visible.",
};

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="text-4xl font-bold mb-8">About MethLab</h1>

      <div className="space-y-12 text-zinc-300">
        {/* Mission */}
        <Section title="Mission">
          <p>
            Methane is the second most impactful greenhouse gas, responsible for
            roughly 30% of global warming to date. Yet most methane emissions are
            invisible - leaks from oil and gas infrastructure, coal mines, landfills,
            and livestock operations that go undetected and unreported.
          </p>
          <p>
            MethLab transforms satellite detection data into immersive 3D
            visualizations that make these invisible emissions impossible to
            ignore. By pairing scientific data with visceral visual impact, we
            aim to drive awareness and action.
          </p>
        </Section>

        {/* How it works */}
        <Section title="How It Works">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StepCard
              number="01"
              title="Satellite Detection"
              description="Imaging spectrometers on satellites like Tanager detect methane and CO2 plumes from orbit by measuring absorption in reflected sunlight."
            />
            <StepCard
              number="02"
              title="Data Processing"
              description="Carbon Mapper processes raw satellite imagery into quantified emission rates (kg/hr), plume geometries, wind data, and source attribution."
            />
            <StepCard
              number="03"
              title="3D Visualization"
              description="We render each plume as a volumetric 3D volume using ray-marched atmospheric scattering, driven by real emission rates and wind vectors."
            />
          </div>
        </Section>

        {/* Technology */}
        <Section title="Technology">
          <p>
            The 3D plume visualizations use volumetric ray-marching adapted from
            geospatial cloud rendering technology. Each plume&apos;s shape is
            generated using the Gaussian plume dispersion model, driven by real
            satellite-measured emission rates and wind data.
          </p>
          <p>
            Key parameters from the satellite data - emission rate (kg/hr), wind
            speed and direction, plume bounds - are mapped to volumetric density,
            scattering coefficients, and advection vectors to create physically
            plausible visualizations.
          </p>
        </Section>

        {/* Data sources */}
        <Section title="Data Sources">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
              <h3 className="text-lg font-bold text-white mb-2">
                Carbon Mapper
              </h3>
              <p className="text-sm text-zinc-400 mb-3">
                Provides satellite-based methane and CO2 plume detection data from
                the Tanager satellite constellation. Over 35,000 plumes
                catalogued globally.
              </p>
              <a
                href="https://carbonmapper.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-orange-400 hover:text-orange-300"
              >
                carbonmapper.org &rarr;
              </a>
            </div>
            <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
              <h3 className="text-lg font-bold text-white mb-2">
                Peregrine Geo Services
              </h3>
              <p className="text-sm text-zinc-400 mb-3">
                Specialists in satellite-based methane detection and monitoring,
                producing detailed reports on fugitive emissions from energy
                infrastructure.
              </p>
              <a
                href="https://www.peregrinegeoservices.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-orange-400 hover:text-orange-300"
              >
                peregrinegeoservices.com &rarr;
              </a>
            </div>
          </div>
        </Section>

        {/* The business case */}
        <Section title="The Business Case">
          <p>
            Most fugitive methane emissions are economically fixable. Leaked
            methane is lost product - natural gas that could be captured and
            sold. The cost of detection, repair, and monitoring is typically a
            fraction of the value of recovered gas and avoided carbon penalties.
          </p>
          <p>
            Our broader mission is ethical natural resource management: helping
            companies identify their emission sources, quantify the cost-benefit
            of remediation, and build a pathway to genuinely lower-emission
            operations.
          </p>
          <Link
            href="/cost-benefit"
            className="inline-block mt-2 text-orange-400 hover:text-orange-300 font-medium"
          >
            Explore the cost-benefit analysis &rarr;
          </Link>
        </Section>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="text-2xl font-bold text-white mb-4">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function StepCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
      <div className="text-3xl font-bold text-orange-500/30 mb-2">
        {number}
      </div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-zinc-400">{description}</p>
    </div>
  );
}
