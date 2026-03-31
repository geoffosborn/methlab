"""
DEKS-embedded methane dashboard.

Serves a self-contained HTML dashboard that runs inside a DEKS iframe.
Reads X-DEKS-Project-Bounds header to find matching facilities and
renders an emissions monitoring dashboard focused on fugitive emissions
detection, targeting, and reduction.
"""

import json
import logging
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    """
    Serve the methane monitoring dashboard.

    When accessed through DEKS proxy, reads X-DEKS-Project-Bounds
    to auto-load emissions data for the project area.
    """
    project_name = request.headers.get("X-DEKS-Project-Name", "")
    project_slug = request.headers.get("X-DEKS-Project-Slug", "")
    bounds = request.query_params.get("bounds", "") or request.headers.get("X-DEKS-Project-Bounds", "")

    # Build the API URL for the frontend to fetch data
    # The dashboard JS will call /deks/project-emissions with the bounds
    api_base = str(request.base_url).rstrip("/")

    # If accessed via proxy, use relative URLs
    prefix = request.headers.get("X-Forwarded-Prefix", "")

    return HTMLResponse(_render_dashboard(
        project_name=project_name,
        project_slug=project_slug,
        bounds=bounds,
        api_base=api_base,
        prefix=prefix,
    ))


def _render_dashboard(
    project_name: str,
    project_slug: str,
    bounds: str,
    api_base: str,
    prefix: str,
) -> str:
    """Render the self-contained dashboard HTML."""

    # Escape for safe embedding in JS
    bounds_js = json.dumps(bounds) if bounds else '""'
    project_name_js = json.dumps(project_name or "Methane Monitoring")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methane Monitoring</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #f8fafc; margin: 0; }}
  .card {{ background: white; border-radius: 12px; border: 1px solid #e2e8f0; }}
  .card-hover {{ transition: all 0.2s; }}
  .card-hover:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-color: #cbd5e1; }}
  .severity-critical {{ color: #dc2626; background: #fef2f2; border-color: #fecaca; }}
  .severity-high {{ color: #ea580c; background: #fff7ed; border-color: #fed7aa; }}
  .severity-medium {{ color: #d97706; background: #fffbeb; border-color: #fde68a; }}
  .severity-low {{ color: #16a34a; background: #f0fdf4; border-color: #bbf7d0; }}
  .trend-increasing {{ color: #dc2626; }}
  .trend-decreasing {{ color: #16a34a; }}
  .trend-stable {{ color: #6b7280; }}
  .pulse {{ animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:0.5 }} }}
  .intensity-bar {{ height: 8px; border-radius: 4px; transition: width 0.8s ease; }}
  .skeleton {{ background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
               background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; }}
  @keyframes shimmer {{ 0% {{ background-position: 200% 0 }} 100% {{ background-position: -200% 0 }} }}
  .detection-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  .dot-high {{ background: #dc2626; }}
  .dot-medium {{ background: #d97706; }}
  .dot-low {{ background: #16a34a; }}
</style>
</head>
<body class="p-4 md:p-6">

<div id="app">
  <!-- Loading state -->
  <div id="loading" class="space-y-4">
    <div class="flex items-center gap-3 mb-6">
      <div class="skeleton w-10 h-10"></div>
      <div>
        <div class="skeleton w-64 h-6 mb-2"></div>
        <div class="skeleton w-40 h-4"></div>
      </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="skeleton h-24"></div><div class="skeleton h-24"></div>
      <div class="skeleton h-24"></div><div class="skeleton h-24"></div>
    </div>
    <div class="skeleton h-64 mt-4"></div>
  </div>

  <!-- No bounds state -->
  <div id="no-bounds" class="hidden">
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">&#x1F30D;</div>
      <h2 class="text-xl font-semibold text-gray-700 mb-2">No geographic bounds set</h2>
      <p class="text-gray-500">This project needs geographic bounds to match methane monitoring facilities.<br>
      Set the project bounds in the project settings to enable emissions monitoring.</p>
    </div>
  </div>

  <!-- No facilities state -->
  <div id="no-facilities" class="hidden">
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">&#x2705;</div>
      <h2 class="text-xl font-semibold text-gray-700 mb-2">No monitored facilities in this area</h2>
      <p class="text-gray-500">No methane monitoring facilities were found within this project's bounds.<br>
      This may mean the area is not yet covered by the monitoring network.</p>
    </div>
  </div>

  <!-- Dashboard content -->
  <div id="dashboard" class="hidden">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"/>
          </svg>
        </div>
        <div>
          <h1 class="text-xl font-bold text-gray-800" id="dash-title">Fugitive Emissions Monitor</h1>
          <p class="text-sm text-gray-500" id="dash-subtitle"></p>
        </div>
      </div>
      <div class="text-xs text-gray-400" id="last-updated"></div>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card p-4">
        <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Facilities</div>
        <div class="text-2xl font-bold text-gray-800" id="stat-facilities">-</div>
        <div class="text-xs text-gray-400" id="stat-facilities-sub">monitored sources</div>
      </div>
      <div class="card p-4">
        <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Peak Intensity</div>
        <div class="text-2xl font-bold" id="stat-intensity">-</div>
        <div class="text-xs text-gray-400" id="stat-intensity-sub">out of 100</div>
      </div>
      <div class="card p-4">
        <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Plume Detections</div>
        <div class="text-2xl font-bold text-gray-800" id="stat-detections">-</div>
        <div class="text-xs text-gray-400" id="stat-detections-sub">total observed</div>
      </div>
      <div class="card p-4">
        <div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Active Alerts</div>
        <div class="text-2xl font-bold" id="stat-alerts">-</div>
        <div class="text-xs text-gray-400" id="stat-alerts-sub">unacknowledged</div>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left column: Facility rankings + trend chart -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Emissions Trend Chart -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Quarterly Emissions Intensity</h3>
          <div style="height: 240px; position: relative;">
            <canvas id="trend-chart"></canvas>
          </div>
        </div>

        <!-- Facility Priority Table -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-1">Emission Source Priority</h3>
          <p class="text-xs text-gray-400 mb-4">Ranked by satellite-derived intensity &mdash; highest emitters first for targeted reduction</p>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs text-gray-500 uppercase tracking-wide border-b border-gray-100">
                  <th class="pb-2 pr-4">#</th>
                  <th class="pb-2 pr-4">Facility</th>
                  <th class="pb-2 pr-4">Intensity</th>
                  <th class="pb-2 pr-4">Enhancement</th>
                  <th class="pb-2 pr-4">Detections</th>
                  <th class="pb-2 pr-4">Trend</th>
                  <th class="pb-2">Compliance</th>
                </tr>
              </thead>
              <tbody id="facility-table"></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Right column: Alerts + Recent detections -->
      <div class="space-y-6">
        <!-- Active Alerts -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Active Alerts</h3>
          <div id="alerts-list" class="space-y-2">
            <p class="text-sm text-gray-400 text-center py-4">No active alerts</p>
          </div>
        </div>

        <!-- Recent Detections -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Recent Plume Detections</h3>
          <div id="detections-list" class="space-y-2">
            <p class="text-sm text-gray-400 text-center py-4">No detections</p>
          </div>
        </div>

        <!-- Compliance Status -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">NGER Compliance</h3>
          <div id="compliance-list" class="space-y-3">
            <p class="text-sm text-gray-400 text-center py-4">No compliance data</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
(function() {{
  const bounds = {bounds_js};
  const projectName = {project_name_js};
  let trendChart = null;

  if (!bounds) {{
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('no-bounds').classList.remove('hidden');
    return;
  }}

  // Fetch emissions data from methlab-api
  const apiUrl = '/deks/project-emissions?bounds=' + encodeURIComponent(bounds) + '&quarters=20';

  // Use relative URL when accessed through proxy, absolute otherwise
  const prefix = '{prefix}';
  const fetchUrl = prefix ? prefix + apiUrl : apiUrl;

  fetch(fetchUrl)
    .then(r => r.json())
    .then(data => {{
      document.getElementById('loading').classList.add('hidden');

      if (data.matched_facilities === 0) {{
        document.getElementById('no-facilities').classList.remove('hidden');
        return;
      }}

      document.getElementById('dashboard').classList.remove('hidden');
      renderDashboard(data);
    }})
    .catch(err => {{
      console.error('Failed to load emissions data:', err);
      document.getElementById('loading').classList.add('hidden');
      document.getElementById('no-facilities').classList.remove('hidden');
    }});

  function renderDashboard(data) {{
    // Title
    document.getElementById('dash-subtitle').textContent =
      projectName + ' \u2014 ' + data.matched_facilities + ' monitored source' + (data.matched_facilities !== 1 ? 's' : '');
    document.getElementById('last-updated').textContent = 'Updated ' + new Date().toLocaleDateString();

    // Summary stats
    document.getElementById('stat-facilities').textContent = data.matched_facilities;

    const maxInt = data.area_summary.max_intensity;
    const intEl = document.getElementById('stat-intensity');
    intEl.textContent = maxInt != null ? Math.round(maxInt) : '\u2014';
    intEl.className = 'text-2xl font-bold ' + (maxInt > 50 ? 'text-red-600' : maxInt > 25 ? 'text-amber-600' : 'text-green-600');

    document.getElementById('stat-detections').textContent = data.area_summary.total_detections;

    const alertCount = data.facilities.reduce((s, f) => s + f.active_alerts.length, 0);
    const alertEl = document.getElementById('stat-alerts');
    alertEl.textContent = alertCount;
    alertEl.className = 'text-2xl font-bold ' + (alertCount > 0 ? 'text-red-600' : 'text-gray-800');

    // Facility priority table
    renderFacilityTable(data.facilities);

    // Trend chart
    renderTrendChart(data.facilities);

    // Alerts
    renderAlerts(data.facilities);

    // Recent detections
    renderDetections(data.facilities);

    // Compliance
    renderCompliance(data.facilities);
  }}

  function renderFacilityTable(facilities) {{
    const tbody = document.getElementById('facility-table');
    tbody.innerHTML = facilities.map((f, i) => {{
      const latest = f.latest_tropomi;
      const intensity = latest?.intensity_score ?? null;
      const enhancement = latest?.mean_enhancement_ppb ?? null;
      const barWidth = intensity != null ? Math.min(intensity, 100) : 0;
      const barColor = intensity > 50 ? '#dc2626' : intensity > 25 ? '#d97706' : '#16a34a';

      const trendIcon = f.trend.direction === 'increasing' ? '\u2191'
        : f.trend.direction === 'decreasing' ? '\u2193' : '\u2192';
      const trendClass = 'trend-' + f.trend.direction;
      const trendLabel = f.trend.change_pct != null
        ? trendIcon + ' ' + Math.abs(f.trend.change_pct) + '%'
        : f.trend.direction === 'insufficient_data' ? '\u2014' : trendIcon;

      const compStatus = f.compliance.status;
      const compBadge = compStatus === 'breach'
        ? '<span class="inline-block px-2 py-0.5 text-xs rounded-full severity-critical">Breach</span>'
        : compStatus === 'warning'
        ? '<span class="inline-block px-2 py-0.5 text-xs rounded-full severity-medium">Warning</span>'
        : compStatus === 'compliant'
        ? '<span class="inline-block px-2 py-0.5 text-xs rounded-full severity-low">OK</span>'
        : '<span class="text-xs text-gray-400">\u2014</span>';

      return '<tr class="border-b border-gray-50 hover:bg-gray-50">' +
        '<td class="py-3 pr-4 text-gray-400 font-mono text-xs">' + (i+1) + '</td>' +
        '<td class="py-3 pr-4"><div class="font-medium text-gray-800">' + f.facility.name + '</div>' +
          '<div class="text-xs text-gray-400">' + (f.facility.operator || '') + '</div></td>' +
        '<td class="py-3 pr-4"><div class="flex items-center gap-2">' +
          '<span class="font-semibold" style="color:' + barColor + '">' + (intensity != null ? Math.round(intensity) : '\u2014') + '</span>' +
          '<div class="w-16 bg-gray-100 rounded-full overflow-hidden intensity-bar">' +
            '<div class="h-full rounded-full" style="width:' + barWidth + '%;background:' + barColor + '"></div>' +
          '</div></div></td>' +
        '<td class="py-3 pr-4 text-gray-600">' + (enhancement != null ? enhancement.toFixed(1) + ' ppb' : '\u2014') + '</td>' +
        '<td class="py-3 pr-4"><span class="font-medium text-gray-800">' + f.total_detections + '</span>' +
          (f.detection_rate_per_year ? '<span class="text-xs text-gray-400 ml-1">(' + f.detection_rate_per_year + '/yr)</span>' : '') + '</td>' +
        '<td class="py-3 pr-4"><span class="font-medium ' + trendClass + '">' + trendLabel + '</span></td>' +
        '<td class="py-3">' + compBadge + '</td></tr>';
    }}).join('');
  }}

  function renderTrendChart(facilities) {{
    // Build datasets - one line per facility
    const colors = ['#dc2626','#2563eb','#d97706','#16a34a','#7c3aed','#db2777','#0891b2','#ea580c'];

    // Collect all unique periods across all facilities
    const allPeriods = new Set();
    facilities.forEach(f => {{
      f.tropomi_trend.forEach(t => allPeriods.add(t.period_start));
    }});
    const sortedPeriods = Array.from(allPeriods).sort();

    // Format labels as "Q1 2019" etc
    const labels = sortedPeriods.map(p => {{
      const d = new Date(p);
      const q = Math.ceil((d.getMonth() + 1) / 3);
      return 'Q' + q + ' ' + d.getFullYear();
    }});

    const datasets = facilities.slice(0, 8).map((f, i) => {{
      const trendMap = {{}};
      f.tropomi_trend.forEach(t => {{ trendMap[t.period_start] = t.intensity_score; }});

      return {{
        label: f.facility.name,
        data: sortedPeriods.map(p => trendMap[p] ?? null),
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length] + '15',
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0.3,
        fill: facilities.length === 1,
        spanGaps: true,
      }};
    }});

    const ctx = document.getElementById('trend-chart').getContext('2d');
    trendChart = new Chart(ctx, {{
      type: 'line',
      data: {{ labels, datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{
            position: 'bottom',
            labels: {{ boxWidth: 12, padding: 16, font: {{ size: 11 }} }}
          }}
        }},
        scales: {{
          y: {{
            beginAtZero: true,
            max: 100,
            title: {{ display: true, text: 'Intensity Score', font: {{ size: 11 }} }},
            grid: {{ color: '#f1f5f9' }}
          }},
          x: {{
            grid: {{ display: false }},
            ticks: {{ font: {{ size: 10 }}, maxRotation: 45 }}
          }}
        }}
      }}
    }});
  }}

  function renderAlerts(facilities) {{
    const allAlerts = facilities.flatMap(f =>
      f.active_alerts.map(a => ({{ ...a, facility_name: f.facility.name }}))
    ).sort((a, b) => {{
      const sev = {{ critical: 0, high: 1, medium: 2, low: 3 }};
      return (sev[a.severity] ?? 4) - (sev[b.severity] ?? 4);
    }});

    const container = document.getElementById('alerts-list');
    if (allAlerts.length === 0) return;

    container.innerHTML = allAlerts.slice(0, 10).map(a => {{
      const sevClass = 'severity-' + a.severity;
      return '<div class="p-3 rounded-lg border ' + sevClass + '">' +
        '<div class="flex items-center justify-between mb-1">' +
          '<span class="text-xs font-semibold uppercase">' + a.severity + '</span>' +
          '<span class="text-xs opacity-60">' + new Date(a.created_at).toLocaleDateString() + '</span>' +
        '</div>' +
        '<div class="text-sm font-medium">' + a.title + '</div>' +
        '<div class="text-xs opacity-70 mt-0.5">' + a.facility_name + '</div>' +
      '</div>';
    }}).join('');
  }}

  function renderDetections(facilities) {{
    const allDet = facilities.flatMap(f =>
      f.recent_detections.map(d => ({{ ...d, facility_name: f.facility.name }}))
    ).sort((a, b) => new Date(b.scene_datetime) - new Date(a.scene_datetime));

    const container = document.getElementById('detections-list');
    if (allDet.length === 0) return;

    container.innerHTML = allDet.slice(0, 8).map(d => {{
      const rate = d.emission_rate_kg_hr;
      const rateStr = rate != null
        ? (rate >= 1000 ? (rate/1000).toFixed(1) + ' t/hr' : Math.round(rate) + ' kg/hr')
        : 'N/A';
      const dotClass = d.confidence === 'high' ? 'dot-high' : d.confidence === 'medium' ? 'dot-medium' : 'dot-low';
      const dt = new Date(d.scene_datetime);
      const dateStr = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit'}});

      return '<div class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">' +
        '<span class="detection-dot ' + dotClass + '" title="' + (d.confidence || 'unknown') + ' confidence"></span>' +
        '<div class="flex-1 min-w-0">' +
          '<div class="text-sm font-medium text-gray-800 truncate">' + d.facility_name + '</div>' +
          '<div class="text-xs text-gray-400">' + dateStr + '</div>' +
        '</div>' +
        '<div class="text-right">' +
          '<div class="text-sm font-semibold text-gray-800">' + rateStr + '</div>' +
          (d.plume_length_m ? '<div class="text-xs text-gray-400">' + (d.plume_length_m/1000).toFixed(1) + ' km plume</div>' : '') +
        '</div>' +
      '</div>';
    }}).join('');
  }}

  function renderCompliance(facilities) {{
    const container = document.getElementById('compliance-list');
    const items = facilities.filter(f => f.compliance.status !== 'no_baseline');

    if (items.length === 0) {{
      container.innerHTML = '<p class="text-sm text-gray-400 text-center py-4">No NGER baselines set</p>';
      return;
    }}

    container.innerHTML = items.map(f => {{
      const c = f.compliance;
      const statusColor = c.status === 'breach' ? 'text-red-600 bg-red-50'
        : c.status === 'warning' ? 'text-amber-600 bg-amber-50'
        : 'text-green-600 bg-green-50';
      const label = c.status === 'breach' ? 'BREACH' : c.status === 'warning' ? 'WARNING' : 'COMPLIANT';

      return '<div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">' +
        '<div>' +
          '<div class="text-sm font-medium text-gray-800">' + f.facility.name + '</div>' +
          '<div class="text-xs text-gray-400">Baseline: ' + (c.nger_baseline ?? '\u2014') + '</div>' +
        '</div>' +
        '<span class="px-2 py-1 text-xs font-semibold rounded-full ' + statusColor + '">' + label + '</span>' +
      '</div>';
    }}).join('');
  }}
}})();
</script>
</body>
</html>"""
