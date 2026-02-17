import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-zinc-950 border-t border-zinc-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center text-white font-bold text-sm">
                M
              </div>
              <span className="text-lg font-bold text-white tracking-tight">
                Meth<span className="text-orange-500">Lab</span>
              </span>
            </div>
            <p className="text-sm text-zinc-500 max-w-xs">
              Making invisible emissions visible. Real satellite data, immersive
              3D visualization, and the business case for fixing leaks.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Explore
            </h3>
            <div className="space-y-2">
              <Link
                href="/leaks"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                Leak of the Week
              </Link>
              <Link
                href="/map"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                Global Map
              </Link>
              <Link
                href="/cost-benefit"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                Cost-Benefit Analysis
              </Link>
              <Link
                href="/about"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                About
              </Link>
            </div>
          </div>

          {/* Data sources */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
              Data Sources
            </h3>
            <div className="space-y-2">
              <a
                href="https://carbonmapper.org"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                Carbon Mapper
              </a>
              <a
                href="https://www.peregrinegeoservices.com"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-zinc-500 hover:text-white transition-colors"
              >
                Peregrine Geo Services
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-zinc-800/50 text-center text-xs text-zinc-600">
          Built with satellite data from Carbon Mapper. Visualization powered by
          three-geospatial.
        </div>
      </div>
    </footer>
  );
}
