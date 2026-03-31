"""
Methane emission rate quantification using the IME method.

Converts segmented plume enhancement maps to emission rates (kg/hr)
using the Integrated Mass Enhancement (IME) approach.

Reference:
    Varon et al. (2018) "Quantifying methane point sources from
    fine-scale satellite observations of atmospheric methane plumes",
    ACP.

    Varon et al. (2021) — Section 2.3: IME method with effective
    wind speed parameterization for Sentinel-2.
"""

import logging
from dataclasses import dataclass

import numpy as np

from sentinel2.download import S2Scene
from sentinel2.radiative import delta_omega_from_enhancement
from sentinel2.segmentation import PlumeSegment

logger = logging.getLogger(__name__)

# Physical constants
CH4_MOLAR_MASS = 16.04e-3  # kg/mol
DRY_AIR_MOLAR_MASS = 28.97e-3  # kg/mol
AVOGADRO = 6.022e23  # mol⁻¹
SURFACE_PRESSURE = 101325  # Pa (standard atmosphere)
G = 9.81  # m/s² gravitational acceleration


@dataclass
class EmissionEstimate:
    """Quantified methane emission rate from a single plume."""

    emission_rate_kg_hr: float  # Emission rate (kg/hr)
    emission_rate_t_hr: float  # Emission rate (t/hr)
    ime_kg: float  # Integrated Mass Enhancement (kg)
    effective_wind_m_s: float  # Effective wind speed (m/s)
    plume_length_m: float  # Effective plume length (m)
    plume_area_m2: float  # Plume area (m²)
    uncertainty_kg_hr: float  # Estimated 1σ uncertainty
    method: str = "IME_Varon2021"


def quantify_emission(
    segment: PlumeSegment,
    scene: S2Scene,
    wind_speed_10m: float,
    pixel_size_m: float = 20.0,
) -> EmissionEstimate:
    """Quantify emission rate for a segmented plume using the IME method.

    IME method (Varon et al. 2018, 2021):
        Q = IME × Ueff / L

    Where:
        IME = Integrated Mass Enhancement (kg CH4 in the plume)
        Ueff = Effective wind speed (m/s)
        L = Effective plume length (m)

    Args:
        segment: Segmented plume with enhancement values
        scene: S2 scene with viewing geometry metadata
        wind_speed_10m: ERA5 10m wind speed (m/s)
        pixel_size_m: S2 pixel size (20m for SWIR bands)

    Returns:
        EmissionEstimate with emission rate and uncertainty
    """
    # Step 1: Convert enhancement (ΔB12/B12) to column density ΔΩ (kg/m²)
    # Using radiative transfer lookup or simplified conversion
    amf = compute_air_mass_factor(scene.solar_zenith, scene.view_zenith)

    # Compute per-pixel mass enhancement
    enhancement_values = segment.mean_enhancement  # Mean ΔB12 in plume
    delta_omega = delta_omega_from_enhancement(enhancement_values, amf)

    # Step 2: IME = sum of ΔΩ × pixel_area over all plume pixels
    pixel_area = pixel_size_m**2  # 400 m² for 20m pixels
    ime_kg = delta_omega * segment.area_m2

    # Step 3: Effective wind speed
    # Varon (2021) S2 validation parameterization:
    # Ueff = 0.33 × U10 + 0.45
    u_eff = 0.33 * wind_speed_10m + 0.45

    # Step 4: Effective plume length
    # Approximate from bounding box extent along wind direction
    bbox = segment.bbox  # (min_row, min_col, max_row, max_col)
    plume_height_px = bbox[2] - bbox[0]
    plume_width_px = bbox[3] - bbox[1]
    plume_length_m = max(plume_height_px, plume_width_px) * pixel_size_m

    # Ensure minimum plume length
    plume_length_m = max(plume_length_m, pixel_size_m)

    # Step 5: Emission rate
    # Q (kg/s) = IME (kg) × Ueff (m/s) / L (m)
    q_kg_s = ime_kg * u_eff / plume_length_m
    q_kg_hr = q_kg_s * 3600

    # Step 6: Uncertainty estimate
    # ~50% relative uncertainty is typical for IME method (Varon 2018)
    # Dominated by wind speed uncertainty and single-overpass variability
    uncertainty = q_kg_hr * 0.5

    return EmissionEstimate(
        emission_rate_kg_hr=q_kg_hr,
        emission_rate_t_hr=q_kg_hr / 1000,
        ime_kg=ime_kg,
        effective_wind_m_s=u_eff,
        plume_length_m=plume_length_m,
        plume_area_m2=segment.area_m2,
        uncertainty_kg_hr=uncertainty,
    )


def compute_air_mass_factor(
    solar_zenith_deg: float,
    view_zenith_deg: float,
) -> float:
    """Compute Air Mass Factor for SWIR column retrieval.

    AMF accounts for the path length through the atmosphere.
    For nadir-ish viewing:
        AMF ≈ 1/cos(θ_sun) + 1/cos(θ_view)

    Args:
        solar_zenith_deg: Solar zenith angle (degrees)
        view_zenith_deg: Viewing zenith angle (degrees)

    Returns:
        Air mass factor (dimensionless, typically 2.0-3.0)
    """
    sza_rad = np.radians(min(solar_zenith_deg, 75))  # Cap at 75°
    vza_rad = np.radians(min(view_zenith_deg, 30))

    amf = 1.0 / np.cos(sza_rad) + 1.0 / np.cos(vza_rad)

    return float(amf)


def xch4_to_column_density(
    delta_xch4_ppm: float,
    surface_pressure_pa: float = SURFACE_PRESSURE,
) -> float:
    """Convert ΔXCH4 (ppm) to column density ΔΩ (kg CH4/m²).

    Using Avogadro's law:
        ΔΩ = ΔXCH4 × (P / g) × (M_CH4 / M_air)

    Args:
        delta_xch4_ppm: CH4 enhancement in ppm
        surface_pressure_pa: Surface pressure in Pa

    Returns:
        Column density enhancement in kg/m²
    """
    delta_xch4_frac = delta_xch4_ppm * 1e-6

    # Total air column: P/g in kg/m²
    total_air_column = surface_pressure_pa / G

    # CH4 column density
    delta_omega = delta_xch4_frac * total_air_column * (CH4_MOLAR_MASS / DRY_AIR_MOLAR_MASS)

    return delta_omega
