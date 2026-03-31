"""
Methane plume segmentation from S2 enhancement maps.

Uses classical image processing (scikit-image) for plume segmentation.
Phase 4 replaces this with a U-Net deep learning model.

Reference:
    Varon et al. (2021) — threshold + morphology approach for
    initial plume delineation before quantification.
"""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion
from skimage.measure import label, regionprops

from sentinel2.config import get_settings
from sentinel2.enhancement import EnhancementResult

logger = logging.getLogger(__name__)


@dataclass
class PlumeSegment:
    """A segmented plume cluster from an enhancement map."""

    label_id: int
    area_pixels: int  # Number of pixels in cluster
    area_m2: float  # Physical area at 20m resolution
    centroid: tuple[float, float]  # (row, col) centroid
    bbox: tuple[int, int, int, int]  # (min_row, min_col, max_row, max_col)
    mean_enhancement: float  # Mean enhancement in cluster
    max_enhancement: float  # Peak enhancement
    total_enhancement: float  # Sum of enhancement values
    mask: np.ndarray  # Boolean mask for this cluster


def segment_plumes(
    result: EnhancementResult,
    min_plume_pixels: int | None = None,
    pixel_size_m: float = 20.0,
) -> list[PlumeSegment]:
    """Segment individual plume clusters from an enhancement result.

    Steps:
    1. Start from the thresholded plume mask
    2. Apply morphological opening (erosion → dilation) to remove noise
    3. Label connected components
    4. Filter by minimum area (default 40 pixels = 16,000 m²)
    5. Extract properties for each cluster

    Args:
        result: Enhancement result with plume_mask
        min_plume_pixels: Minimum pixels per cluster
        pixel_size_m: Pixel size in meters (S2 SWIR = 20m)

    Returns:
        List of PlumeSegment objects, sorted by area (largest first)
    """
    settings = get_settings()
    if min_plume_pixels is None:
        min_plume_pixels = settings.min_plume_pixels

    mask = result.plume_mask.copy()

    # Morphological opening: remove small noise blobs
    struct = np.ones((3, 3))
    mask = binary_erosion(mask, structure=struct, iterations=1)
    mask = binary_dilation(mask, structure=struct, iterations=1)

    # Label connected components
    labeled, n_labels = label(mask, return_num=True)

    if n_labels == 0:
        logger.debug("No plume clusters found after morphological filtering")
        return []

    # Extract region properties
    segments = []
    for region in regionprops(labeled, intensity_image=result.enhancement):
        if region.area < min_plume_pixels:
            continue

        cluster_mask = labeled == region.label
        enhancement_values = result.enhancement[cluster_mask]
        valid = ~np.isnan(enhancement_values)

        if valid.sum() == 0:
            continue

        segments.append(
            PlumeSegment(
                label_id=region.label,
                area_pixels=region.area,
                area_m2=region.area * pixel_size_m**2,
                centroid=(region.centroid[0], region.centroid[1]),
                bbox=region.bbox,
                mean_enhancement=float(np.mean(enhancement_values[valid])),
                max_enhancement=float(np.max(enhancement_values[valid])),
                total_enhancement=float(np.sum(enhancement_values[valid])),
                mask=cluster_mask,
            )
        )

    # Sort by area (largest first)
    segments.sort(key=lambda s: s.area_pixels, reverse=True)

    logger.info(
        "Segmented %d plume clusters (of %d components, min %d px) for %s",
        len(segments), n_labels, min_plume_pixels, result.scene_id,
    )

    return segments
