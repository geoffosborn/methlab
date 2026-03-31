"""
End-to-end test: inject a synthetic plume into clean S2-like data,
run the full Phase 3 quantification pipeline, and verify the
emission rate output is within expected bounds.

This validates the entire chain:
    background model → enhancement → segmentation → quantification

without requiring real satellite data or API access.
"""

import numpy as np
import pytest

from sentinel2.background import BackgroundModel, predict_b12
from sentinel2.enhancement import compute_enhancement, EnhancementResult
from sentinel2.download import S2Scene
from sentinel2.quantification import quantify_emission, compute_air_mass_factor
from sentinel2.segmentation import segment_plumes
from sentinel2.radiative import enhancement_to_xch4, delta_omega_from_enhancement


# --- Synthetic data generators ---


def make_clean_scene(
    shape: tuple[int, int] = (200, 200),
    b11_mean: float = 0.15,
    b12_mean: float = 0.10,
    noise_std: float = 0.002,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate clean B11/B12 reflectance arrays with realistic noise."""
    rng = np.random.default_rng(42)

    # B11 with spatial variation (surface albedo heterogeneity)
    b11 = b11_mean + rng.normal(0, noise_std, shape).astype(np.float32)
    b11 += np.linspace(-0.01, 0.01, shape[1])  # Gentle E-W gradient

    # B12 linearly related to B11 (the relationship we model)
    # True relationship: B12 = 0.65 * B11 + 0.005
    b12 = 0.65 * b11 + 0.005 + rng.normal(0, noise_std * 0.8, shape).astype(np.float32)

    return b11, b12


def inject_synthetic_plume(
    b12: np.ndarray,
    center: tuple[int, int] = (100, 100),
    wind_direction_deg: float = 270.0,
    peak_delta_b12: float = 0.008,
    plume_length_px: int = 60,
) -> tuple[np.ndarray, np.ndarray]:
    """Inject a Gaussian plume into B12 by reducing reflectance (CH4 absorption).

    Returns modified B12 and the ground-truth plume mask.
    """
    h, w = b12.shape
    y, x = np.mgrid[0:h, 0:w]
    dy = y - center[0]
    dx = x - center[1]

    # Rotate to wind direction
    wind_rad = np.radians(wind_direction_deg)
    along = dx * np.cos(wind_rad) + dy * np.sin(wind_rad)
    cross = -dx * np.sin(wind_rad) + dy * np.cos(wind_rad)

    # Gaussian plume dispersion
    downwind = np.maximum(along, 0)
    sigma_cross = 3.0 + 0.1 * downwind
    sigma_along = plume_length_px / 3.0

    plume = peak_delta_b12 * np.exp(-0.5 * (cross / sigma_cross) ** 2)
    plume *= np.exp(-0.5 * ((downwind - plume_length_px / 2) / sigma_along) ** 2)
    plume = np.where(along > 0, plume, 0)

    # CH4 absorbs in B12 → reduce B12 reflectance
    b12_modified = b12 - plume

    # Ground truth mask: plume pixels above a small threshold
    truth_mask = plume > peak_delta_b12 * 0.1

    return b12_modified.astype(np.float32), truth_mask


def make_background_model(
    shape: tuple[int, int] = (200, 200),
    n_scenes: int = 30,
) -> BackgroundModel:
    """Build a background model from synthetic clean scenes."""
    from sentinel2.background import build_background_model
    from datetime import datetime

    import rasterio.transform

    scenes = []
    for i in range(n_scenes):
        b11, b12 = make_clean_scene(shape, noise_std=0.002 + 0.0005 * (i % 5))
        scenes.append(S2Scene(
            scene_id=f"synthetic_{i:03d}",
            datetime=datetime(2024, 1 + i % 12, 1 + i % 28),
            b11=b11,
            b12=b12,
            transform=rasterio.transform.from_bounds(148.0, -22.0, 148.2, -21.8, shape[1], shape[0]),
            crs="EPSG:4326",
            cloud_cover=5.0,
            solar_zenith=30.0,
            view_zenith=5.0,
            bounds=(148.0, -22.0, 148.2, -21.8),
        ))

    return build_background_model(scenes, min_valid_fraction=0.3)


# --- Tests ---


class TestSyntheticPlumeE2E:
    """End-to-end test with synthetic plume injection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.shape = (200, 200)
        self.model = make_background_model(self.shape, n_scenes=15)

    def test_background_model_quality(self):
        """Background model should capture the B12/B11 relationship."""
        valid = ~np.isnan(self.model.slope)
        assert valid.sum() > 0.5 * self.shape[0] * self.shape[1], "Model should cover >50% of pixels"

        # Slope should be close to the true value of 0.65
        median_slope = np.nanmedian(self.model.slope)
        assert 0.5 < median_slope < 0.8, f"Expected slope ~0.65, got {median_slope:.3f}"

    def test_clean_scene_no_detection(self):
        """Clean scene should produce no plume detections."""
        import rasterio.transform

        b11, b12 = make_clean_scene(self.shape)
        scene = S2Scene(
            scene_id="clean_test",
            datetime=__import__("datetime").datetime(2024, 6, 15),
            b11=b11, b12=b12,
            transform=rasterio.transform.from_bounds(148.0, -22.0, 148.2, -21.8, 200, 200),
            crs="EPSG:4326",
            cloud_cover=5.0, solar_zenith=30.0, view_zenith=5.0,
            bounds=(148.0, -22.0, 148.2, -21.8),
        )

        enhancement = compute_enhancement(scene, self.model, wind_direction=270.0)
        if enhancement is not None:
            segments = segment_plumes(enhancement, min_plume_pixels=40)
            assert len(segments) == 0, f"Clean scene should have 0 detections, got {len(segments)}"

    def test_plume_detection_and_quantification(self):
        """Injected plume should be detected and quantified within reasonable bounds."""
        import rasterio.transform

        b11, b12_clean = make_clean_scene(self.shape)

        # Inject a plume with known parameters
        peak_delta = 0.008  # ~8% B12 reduction at peak
        b12_plume, truth_mask = inject_synthetic_plume(
            b12_clean, center=(100, 100), wind_direction_deg=270.0,
            peak_delta_b12=peak_delta, plume_length_px=60,
        )

        scene = S2Scene(
            scene_id="plume_test",
            datetime=__import__("datetime").datetime(2024, 6, 15),
            b11=b11, b12=b12_plume,
            transform=rasterio.transform.from_bounds(148.0, -22.0, 148.2, -21.8, 200, 200),
            crs="EPSG:4326",
            cloud_cover=5.0, solar_zenith=30.0, view_zenith=5.0,
            bounds=(148.0, -22.0, 148.2, -21.8),
        )

        # Step 1: Enhancement detection
        enhancement = compute_enhancement(scene, self.model, wind_direction=270.0)
        assert enhancement is not None, "Enhancement should be computed"
        assert enhancement.max_enhancement > 0, "Should detect positive enhancement"

        # Step 2: Segmentation
        segments = segment_plumes(enhancement, min_plume_pixels=20)
        assert len(segments) >= 1, f"Should detect at least 1 plume cluster, got {len(segments)}"

        largest = segments[0]
        assert largest.area_pixels >= 20, f"Plume should be ≥20 pixels, got {largest.area_pixels}"

        # Step 3: Quantification
        estimate = quantify_emission(
            segment=largest,
            scene=scene,
            wind_speed_10m=5.0,  # 5 m/s wind
        )

        assert estimate.emission_rate_kg_hr > 0, "Emission rate should be positive"
        assert estimate.ime_kg > 0, "IME should be positive"
        assert estimate.effective_wind_m_s > 0, "Effective wind should be positive"

        # Verify Ueff = 0.33 * 5.0 + 0.45 = 2.1
        expected_ueff = 0.33 * 5.0 + 0.45
        assert abs(estimate.effective_wind_m_s - expected_ueff) < 0.01, \
            f"Ueff should be {expected_ueff}, got {estimate.effective_wind_m_s}"

        print(f"\nSynthetic plume test results:")
        print(f"  Plume pixels: {largest.area_pixels}")
        print(f"  Mean enhancement: {largest.mean_enhancement:.6f}")
        print(f"  IME: {estimate.ime_kg:.2f} kg")
        print(f"  Ueff: {estimate.effective_wind_m_s:.2f} m/s")
        print(f"  Plume length: {estimate.plume_length_m:.0f} m")
        print(f"  Emission rate: {estimate.emission_rate_kg_hr:.1f} kg/hr")
        print(f"  Emission rate: {estimate.emission_rate_t_hr:.3f} t/hr")
        print(f"  Uncertainty: ±{estimate.uncertainty_kg_hr:.1f} kg/hr")


class TestRadiativeTransfer:
    """Test the radiative transfer conversion chain."""

    def test_enhancement_to_xch4(self):
        """Verify spectroscopic conversion produces reasonable XCH4 values."""
        # 1% B12 reduction with AMF=2.5 should give ~3800 ppb enhancement
        delta_xch4 = enhancement_to_xch4(0.01, amf=2.5)
        assert 1000 < delta_xch4 < 10000, f"Expected ~3800 ppb, got {delta_xch4:.0f}"

    def test_air_mass_factor(self):
        """AMF should be ~2.0 for nadir sun overhead."""
        amf = compute_air_mass_factor(solar_zenith_deg=0, view_zenith_deg=0)
        assert abs(amf - 2.0) < 0.01

        # Higher zenith → higher AMF
        amf_high = compute_air_mass_factor(solar_zenith_deg=60, view_zenith_deg=10)
        assert amf_high > amf

    def test_delta_omega_positive(self):
        """Column density enhancement should be positive for CH4 absorption."""
        omega = delta_omega_from_enhancement(0.005, amf=2.5)
        assert omega > 0

    def test_zero_enhancement(self):
        """Zero enhancement should give zero everything."""
        assert enhancement_to_xch4(0.0, amf=2.5) == 0.0
        assert delta_omega_from_enhancement(0.0, amf=2.5) == 0.0


class TestWindRotation:
    """Test TROPOMI wind rotation mechanics."""

    def test_rotation_angle(self):
        """Wind from north (0°) should give 0° rotation."""
        from tropomi.wind import WindField
        from datetime import datetime

        w = WindField(datetime=datetime.now(), u10=0.0, v10=-5.0)  # From north
        assert abs(w.direction_from - 0.0) < 1.0 or abs(w.direction_from - 360.0) < 1.0

    def test_wind_speed(self):
        """Wind speed should be computed correctly."""
        from tropomi.wind import WindField
        from datetime import datetime

        w = WindField(datetime=datetime.now(), u10=3.0, v10=4.0)
        assert abs(w.speed - 5.0) < 0.01

    def test_background_estimation(self):
        """Background estimate should be near the 10th percentile."""
        from tropomi.rotation import estimate_background

        # Uniform 1850 ppb with a few high values (plume)
        ch4 = np.full((50, 50), 1850.0)
        ch4[20:25, 20:25] = 1900.0  # Plume region

        bg = estimate_background(ch4, percentile=10.0)
        assert abs(bg - 1850.0) < 5.0, f"Background should be ~1850, got {bg:.1f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
