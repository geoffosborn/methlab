"""
TROPOMI CH4 visualization — wind-rotated tear sheet PNGs and GeoTIFFs.

Generates publication-quality visualizations of wind-rotated CH4 anomaly
fields for facility monitoring reports, plus georeferenced GeoTIFF outputs
for GIS integration.
"""

import io
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import rasterio
from rasterio.transform import from_bounds

from tropomi.metrics import TropomiMetrics

logger = logging.getLogger(__name__)

# Color map: blue (low) -> white (zero) -> yellow -> orange -> red (high)
METHANE_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "methane",
    [
        (0.0, "#2166ac"),    # Blue (negative/background)
        (0.35, "#f7f7f7"),   # White (near zero)
        (0.5, "#fddbc7"),    # Light orange
        (0.7, "#f4a582"),    # Orange
        (0.85, "#d6604d"),   # Red-orange
        (1.0, "#b2182b"),    # Dark red (high enhancement)
    ],
)


def render_tear_sheet(
    averaged_field: np.ndarray,
    metrics: TropomiMetrics,
    facility_name: str,
    period_label: str,
    pixel_size_km: float = 5.0,
    output_path: str | Path | None = None,
) -> bytes:
    """Render a wind-rotated CH4 tear sheet visualization.

    Creates a figure with:
    - Wind-rotated CH4 anomaly field with color scale
    - Facility location marker at center
    - Wind direction arrow (pointing north = downwind after rotation)
    - Metrics panel with key statistics
    - Title with facility name and period

    Args:
        averaged_field: 2D averaged CH4 anomaly (ppb)
        metrics: Computed metrics for the period
        facility_name: Name of facility for title
        period_label: Time period label (e.g., "2024 Q3", "2024")
        pixel_size_km: Grid pixel size in km
        output_path: Optional file path to save PNG

    Returns:
        PNG image bytes
    """
    grid_size = averaged_field.shape[0]
    extent_km = grid_size * pixel_size_km / 2

    fig, (ax_map, ax_stats) = plt.subplots(
        1, 2,
        figsize=(14, 7),
        gridspec_kw={"width_ratios": [2, 1]},
        facecolor="#1a1a2e",
    )

    # --- CH4 anomaly map ---
    ax_map.set_facecolor("#1a1a2e")

    # Auto-scale colormap to actual data range
    valid_data = averaged_field[~np.isnan(averaged_field)]
    if len(valid_data) > 0:
        p95 = float(np.percentile(valid_data, 95))
        p5 = float(np.percentile(valid_data, 5))
        vmax = max(abs(p95), abs(p5), 3.0)
    else:
        vmax = 10.0

    im = ax_map.imshow(
        averaged_field,
        cmap=METHANE_CMAP,
        vmin=-vmax * 0.4,
        vmax=vmax,
        origin="lower",
        extent=[-extent_km, extent_km, -extent_km, extent_km],
        interpolation="gaussian",
    )

    # Facility marker at center
    ax_map.plot(0, 0, "k+", markersize=15, markeredgewidth=2)
    ax_map.plot(0, 0, "w+", markersize=12, markeredgewidth=1.5)

    # Wind direction arrow (pointing north = downwind)
    arrow_y = extent_km * 0.75
    ax_map.annotate(
        "",
        xy=(0, arrow_y),
        xytext=(0, arrow_y * 0.6),
        arrowprops=dict(arrowstyle="->", color="white", lw=2),
    )
    ax_map.text(
        0, arrow_y + extent_km * 0.05,
        "Wind",
        ha="center", va="bottom",
        color="white", fontsize=9, fontweight="bold",
    )

    # Colorbar
    cbar = fig.colorbar(im, ax=ax_map, shrink=0.8, pad=0.02)
    cbar.set_label("CH4 Enhancement (ppb)", color="white", fontsize=10)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    ax_map.set_xlabel("Distance (km)", color="white", fontsize=10)
    ax_map.set_ylabel("Distance (km)", color="white", fontsize=10)
    ax_map.tick_params(colors="white")
    ax_map.set_title(
        f"{facility_name}\nWind-Rotated CH4 — {period_label}",
        color="white", fontsize=13, fontweight="bold", pad=12,
    )

    # Scale reference
    scale_len = 25 if extent_km < 200 else 50
    scale_x = extent_km * 0.4
    scale_y = -extent_km * 0.85
    ax_map.plot([scale_x, scale_x + scale_len], [scale_y, scale_y], "w-", lw=2)
    ax_map.text(
        scale_x + scale_len / 2, scale_y - extent_km * 0.04,
        f"{scale_len} km", ha="center", color="white", fontsize=8,
    )

    # --- Stats panel ---
    ax_stats.set_facecolor("#1a1a2e")
    ax_stats.axis("off")

    stats_text = [
        ("Mean Enhancement", f"{metrics.mean_enhancement_ppb:.1f} ppb"),
        ("Peak Enhancement", f"{metrics.max_enhancement_ppb:.1f} ppb"),
        ("Central Box Mean", f"{metrics.central_box_mean_ppb:.1f} ppb"),
        ("", ""),
        ("Intensity Score", f"{metrics.intensity_score:.0f} / 100"),
        ("", ""),
        ("Overpasses", f"{metrics.sample_count}"),
        ("Valid Coverage", f"{metrics.valid_pixel_fraction:.0%}"),
        ("Mean Wind Speed", f"{metrics.mean_wind_speed:.1f} m/s"),
        ("Background CH4", f"{metrics.background_ch4_ppb:.0f} ppb"),
    ]

    y_pos = 0.9
    for label, value in stats_text:
        if not label:
            y_pos -= 0.03
            continue
        ax_stats.text(0.05, y_pos, label, color="#999", fontsize=10,
                      transform=ax_stats.transAxes, va="top")
        ax_stats.text(0.95, y_pos, value, color="white", fontsize=11,
                      fontweight="bold", transform=ax_stats.transAxes,
                      va="top", ha="right")
        y_pos -= 0.07

    # Intensity bar
    y_pos -= 0.03
    bar_y = y_pos
    bar_width = 0.9
    ax_stats.barh(
        bar_y, metrics.intensity_score / 100 * bar_width,
        height=0.03, left=0.05,
        color=_intensity_color(metrics.intensity_score),
        transform=ax_stats.transAxes,
    )
    ax_stats.barh(
        bar_y, bar_width, height=0.03, left=0.05,
        color="none", edgecolor="#444",
        transform=ax_stats.transAxes,
    )

    # Data source attribution
    ax_stats.text(
        0.5, 0.02,
        "Data: Sentinel-5P TROPOMI / Copernicus\nWind: ERA5 / ECMWF\nProcessing: MethLab / GeoSynergy",
        ha="center", va="bottom", color="#555", fontsize=7,
        transform=ax_stats.transAxes, linespacing=1.5,
    )

    plt.tight_layout()

    # Save to bytes
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    png_bytes = buf.read()

    # Optionally save to file
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(png_bytes)
        logger.info("Saved tear sheet to %s", output_path)

    return png_bytes


def export_geotiff(
    averaged_field: np.ndarray,
    center_lat: float,
    center_lon: float,
    output_path: str | Path,
    pixel_size_km: float = 5.0,
) -> Path:
    """Export wind-rotated CH4 anomaly field as a GeoTIFF with transparent background.

    NaN pixels are written as nodata (transparent in GIS).
    CRS is EPSG:4326 (WGS84 lat/lon).

    Args:
        averaged_field: 2D CH4 anomaly array (ppb above background)
        center_lat: Facility latitude
        center_lon: Facility longitude
        output_path: Output file path
        pixel_size_km: Grid pixel size in km

    Returns:
        Path to written GeoTIFF
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grid_size = averaged_field.shape[0]
    extent_km = grid_size * pixel_size_km / 2

    # Convert km extent to degrees
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * np.cos(np.radians(center_lat))

    west = center_lon - extent_km / km_per_deg_lon
    east = center_lon + extent_km / km_per_deg_lon
    south = center_lat - extent_km / km_per_deg_lat
    north = center_lat + extent_km / km_per_deg_lat

    transform = from_bounds(west, south, east, north, grid_size, grid_size)

    # Flip vertically — imshow origin="lower" but GeoTIFF is top-down
    data = np.flipud(averaged_field).astype(np.float32)

    nodata = -9999.0
    data = np.where(np.isnan(data), nodata, data)

    with rasterio.open(
        str(output_path),
        "w",
        driver="GTiff",
        height=grid_size,
        width=grid_size,
        count=1,
        dtype="float32",
        crs=rasterio.crs.CRS.from_wkt('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'),
        transform=transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(data, 1)
        dst.update_tags(
            PROCESSING="MethLab / GeoSynergy",
            DATA_SOURCE="Sentinel-5P TROPOMI / Copernicus",
            WIND_SOURCE="ERA5 / ECMWF",
            UNITS="ppb CH4 enhancement above background",
        )

    logger.info("Exported GeoTIFF to %s", output_path)
    return output_path


def _intensity_color(score: float) -> str:
    """Map intensity score to color."""
    if score >= 70:
        return "#ef4444"  # Red — high
    elif score >= 40:
        return "#f59e0b"  # Amber — moderate
    elif score >= 15:
        return "#3b82f6"  # Blue — low
    else:
        return "#22c55e"  # Green — minimal
