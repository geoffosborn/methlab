"""
Radiative transfer lookup tables for SWIR CH4 retrieval.

Maps B12/B11 reflectance ratios to CH4 column concentration using
precomputed lookup tables. Accounts for variable Air Mass Factor.

Initially uses published empirical values from Varon et al. (2021).
Phase 4 enhancement: generate LUTs with libRadtran for site-specific
atmospheric profiles.

Reference:
    Varon et al. (2021) — Supplementary: "The sensitivity of
    B12 reflectance to CH4 column enhancement..."
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Empirical sensitivity coefficients from Varon et al. (2021)
# ΔB12/B12 ≈ -α × ΔXCH4 × AMF
# Where α is the CH4 absorption coefficient at 2190nm
#
# Published value: α ≈ 2.6e-9 per ppb per unit AMF
# This means a 1000 ppb XCH4 enhancement with AMF=2.5 gives
# ΔB12/B12 ≈ -6.5e-3 (0.65% decrease in B12 reflectance)
ALPHA_CH4_2190NM = 2.6e-9  # Absorption coefficient (per ppb per AMF)

# Physical constants
CH4_MOLAR_MASS = 16.04e-3  # kg/mol
DRY_AIR_MOLAR_MASS = 28.97e-3  # kg/mol
G = 9.81  # m/s²
SURFACE_PRESSURE = 101325  # Pa


def enhancement_to_xch4(
    delta_b12_ratio: float,
    amf: float,
) -> float:
    """Convert B12 enhancement ratio to ΔXCH4 (ppb).

    Args:
        delta_b12_ratio: ΔB12/B12 enhancement (positive for CH4 absorption)
        amf: Air Mass Factor

    Returns:
        ΔXCH4 in ppb
    """
    if amf <= 0:
        return 0.0

    # ΔB12/B12 = -α × ΔXCH4 × AMF
    # Therefore: ΔXCH4 = -ΔB12/B12 / (α × AMF)
    # Our enhancement is defined as predicted - observed (positive = absorption)
    # so delta_b12_ratio is positive for CH4
    delta_xch4 = delta_b12_ratio / (ALPHA_CH4_2190NM * amf)

    return float(max(0, delta_xch4))


def delta_omega_from_enhancement(
    delta_b12_ratio: float,
    amf: float,
) -> float:
    """Convert B12 enhancement directly to column density ΔΩ (kg CH4/m²).

    Combines spectroscopic conversion and column density calculation
    in one step.

    Args:
        delta_b12_ratio: ΔB12/B12 enhancement
        amf: Air Mass Factor

    Returns:
        Column density enhancement in kg CH4/m²
    """
    # Get ΔXCH4 in ppb
    delta_xch4_ppb = enhancement_to_xch4(delta_b12_ratio, amf)

    # Convert to mixing ratio fraction
    delta_xch4_frac = delta_xch4_ppb * 1e-9  # ppb to fraction

    # Total air column mass: P/g (kg/m²)
    total_air_column = SURFACE_PRESSURE / G  # ~10329 kg/m²

    # CH4 column density
    delta_omega = delta_xch4_frac * total_air_column * (CH4_MOLAR_MASS / DRY_AIR_MOLAR_MASS)

    return float(delta_omega)


def build_lut(
    amf_range: tuple[float, float] = (1.5, 4.0),
    amf_steps: int = 50,
    enhancement_range: tuple[float, float] = (0.0, 0.05),
    enhancement_steps: int = 100,
) -> dict:
    """Build a 2D lookup table mapping (AMF, ΔB12/B12) → (ΔXCH4, ΔΩ).

    For fast runtime lookup instead of per-pixel calculation.

    Returns:
        Dict with arrays: amf_grid, enhancement_grid, xch4_grid, omega_grid
    """
    amf_vals = np.linspace(amf_range[0], amf_range[1], amf_steps)
    enh_vals = np.linspace(enhancement_range[0], enhancement_range[1], enhancement_steps)

    amf_grid, enh_grid = np.meshgrid(amf_vals, enh_vals, indexing="ij")

    xch4_grid = np.zeros_like(amf_grid)
    omega_grid = np.zeros_like(amf_grid)

    for i in range(amf_steps):
        for j in range(enhancement_steps):
            xch4_grid[i, j] = enhancement_to_xch4(enh_vals[j], amf_vals[i])
            omega_grid[i, j] = delta_omega_from_enhancement(enh_vals[j], amf_vals[i])

    return {
        "amf": amf_vals,
        "enhancement": enh_vals,
        "xch4_ppb": xch4_grid,
        "delta_omega_kg_m2": omega_grid,
    }
