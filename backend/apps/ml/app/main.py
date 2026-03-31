"""
MethLab ML Inference Service
FastAPI Application — Port 8023
GPU instance (g4dn.xlarge recommended)

Provides batch and single inference endpoints for:
- U-Net plume segmentation
- EfficientNet plume/flare/negative classification
- TROPOMI CNN daily plume detection
"""

import io
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from ml.models.classifier import PlumeClassifier
from ml.models.tropomi_cnn import TropomiCNN
from ml.models.unet import PlumeUNet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = 8023
    debug: bool = False
    model_dir: str = "/data/methlab/models"
    device: str = "cuda"  # cuda or cpu


settings = Settings()

# Global model registry
models: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    device = torch.device(settings.device if torch.cuda.is_available() else "cpu")
    logger.info("ML Inference starting on %s (device: %s)", settings.port, device)

    model_dir = Path(settings.model_dir)

    # Load U-Net
    unet_path = model_dir / "unet" / "best_model.pth"
    if unet_path.exists():
        unet = PlumeUNet(in_channels=3).to(device)
        unet.load_state_dict(torch.load(unet_path, map_location=device, weights_only=True))
        unet.eval()
        models["unet"] = unet
        logger.info("Loaded U-Net from %s", unet_path)

    # Load classifier
    clf_path = model_dir / "classifier" / "best_model.pth"
    if clf_path.exists():
        clf = PlumeClassifier().to(device)
        clf.load_state_dict(torch.load(clf_path, map_location=device, weights_only=True))
        clf.eval()
        models["classifier"] = clf
        logger.info("Loaded classifier from %s", clf_path)

    # Load TROPOMI CNN
    cnn_path = model_dir / "tropomi_cnn" / "best_model.pth"
    if cnn_path.exists():
        cnn = TropomiCNN().to(device)
        cnn.load_state_dict(torch.load(cnn_path, map_location=device, weights_only=True))
        cnn.eval()
        models["tropomi_cnn"] = cnn
        logger.info("Loaded TROPOMI CNN from %s", cnn_path)

    if not models:
        logger.warning("No models found in %s — inference endpoints will return 503", model_dir)

    yield

    models.clear()
    logger.info("ML Inference shutting down")


app = FastAPI(
    title="MethLab ML Inference",
    description="GPU inference service for methane plume detection models",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    from methlab_common import health_response

    return health_response(
        "methlab-ml",
        models_loaded=list(models.keys()),
        gpu_available=torch.cuda.is_available(),
        gpu_name=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    )


# --- Segmentation endpoint ---


class SegmentationRequest(BaseModel):
    b11: list[list[float]]
    b12: list[list[float]]
    enhancement: list[list[float]]
    threshold: float = 0.5


class SegmentationResponse(BaseModel):
    mask: list[list[float]]
    plume_pixels: int
    plume_fraction: float


@app.post("/predict/segment", response_model=SegmentationResponse)
async def predict_segment(req: SegmentationRequest):
    """Run U-Net plume segmentation."""
    if "unet" not in models:
        raise HTTPException(503, "U-Net model not loaded")

    b11 = np.array(req.b11, dtype=np.float32)
    b12 = np.array(req.b12, dtype=np.float32)
    enhancement = np.array(req.enhancement, dtype=np.float32)

    prob_map = models["unet"].predict(b11, b12, enhancement)
    mask = (prob_map > req.threshold).astype(float)

    plume_pixels = int(mask.sum())
    total_pixels = mask.size

    return SegmentationResponse(
        mask=mask.tolist(),
        plume_pixels=plume_pixels,
        plume_fraction=plume_pixels / total_pixels,
    )


# --- Classification endpoint ---


class ClassificationRequest(BaseModel):
    patch: list[list[list[float]]]  # (C, H, W)


class ClassificationResponse(BaseModel):
    predicted_class: str
    confidence: float
    probabilities: dict[str, float]


@app.post("/predict/classify", response_model=ClassificationResponse)
async def predict_classify(req: ClassificationRequest):
    """Run plume/flare/negative classification."""
    if "classifier" not in models:
        raise HTTPException(503, "Classifier model not loaded")

    patch = np.array(req.patch, dtype=np.float32)
    result = models["classifier"].predict(patch)

    return ClassificationResponse(**result)


# --- TROPOMI detection endpoint ---


class TropomiDetectionRequest(BaseModel):
    ch4_anomaly: list[list[float]]  # (H, W) CH4 anomaly in ppb


class TropomiDetectionResponse(BaseModel):
    plume_probability: float
    is_plume: bool
    confidence: float


@app.post("/predict/tropomi", response_model=TropomiDetectionResponse)
async def predict_tropomi(req: TropomiDetectionRequest):
    """Run TROPOMI daily plume detection."""
    if "tropomi_cnn" not in models:
        raise HTTPException(503, "TROPOMI CNN model not loaded")

    ch4 = np.array(req.ch4_anomaly, dtype=np.float32)
    result = models["tropomi_cnn"].predict(ch4)

    return TropomiDetectionResponse(**result)


# --- Batch endpoint ---


class BatchRequest(BaseModel):
    model: str  # "unet", "classifier", "tropomi_cnn"
    items: list[dict]  # List of individual request payloads


@app.post("/predict/batch")
async def predict_batch(req: BatchRequest):
    """Batch inference for any model."""
    if req.model not in models:
        raise HTTPException(503, f"Model '{req.model}' not loaded")

    results = []
    for item in req.items:
        if req.model == "tropomi_cnn":
            ch4 = np.array(item["ch4_anomaly"], dtype=np.float32)
            results.append(models["tropomi_cnn"].predict(ch4))
        elif req.model == "classifier":
            patch = np.array(item["patch"], dtype=np.float32)
            results.append(models["classifier"].predict(patch))

    return {"results": results, "count": len(results)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
