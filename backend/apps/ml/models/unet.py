"""
U-Net for Sentinel-2 methane plume segmentation.

Replaces the scikit-image threshold+morphology approach from Phase 3
with a learned segmentation model. Trained on published plume datasets
plus synthetic Gaussian plumes for data augmentation.

Architecture:
    - Encoder: ResNet-34 pretrained on ImageNet
    - Decoder: U-Net with skip connections
    - Input: 2-channel (B11, B12) or 3-channel (B11, B12, enhancement)
    - Output: Binary plume mask (H×W)

Training data:
    - Published S2 methane plume datasets
    - Synthetic plumes: Gaussian dispersion model injected into clean scenes
    - Hard negatives: clouds, terrain edges, flares

Reference:
    Rouet-Leduc et al. (2021) — U-Net for satellite methane detection.
"""

import logging
from pathlib import Path

import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)


class PlumeUNet(nn.Module):
    """U-Net for binary plume segmentation from S2 SWIR bands."""

    def __init__(self, in_channels: int = 3, encoder_name: str = "resnet34"):
        super().__init__()
        self.model = smp.Unet(
            encoder_name=encoder_name,
            encoder_weights="imagenet" if in_channels == 3 else None,
            in_channels=in_channels,
            classes=1,
            activation=None,  # Raw logits; sigmoid applied in forward
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (B, C, H, W) input tensor. C=3: [B11, B12, enhancement]

        Returns:
            (B, 1, H, W) sigmoid probability map
        """
        logits = self.model(x)
        return torch.sigmoid(logits)

    def predict(self, b11: np.ndarray, b12: np.ndarray, enhancement: np.ndarray) -> np.ndarray:
        """Run inference on numpy arrays.

        Args:
            b11: (H, W) B11 reflectance
            b12: (H, W) B12 reflectance
            enhancement: (H, W) B12 enhancement map

        Returns:
            (H, W) probability map [0, 1]
        """
        self.eval()
        device = next(self.parameters()).device

        # Stack channels and add batch dim
        x = np.stack([b11, b12, enhancement], axis=0)
        x = torch.from_numpy(x).float().unsqueeze(0).to(device)

        with torch.no_grad():
            prob = self(x)

        return prob.squeeze().cpu().numpy()


class PlumeDataset(Dataset):
    """Dataset for plume segmentation training."""

    def __init__(
        self,
        data_dir: str | Path,
        split: str = "train",
        augment: bool = True,
    ):
        self.data_dir = Path(data_dir)
        self.split = split
        self.augment = augment and split == "train"

        # Load file list
        split_file = self.data_dir / f"{split}.txt"
        if split_file.exists():
            self.samples = split_file.read_text().strip().split("\n")
        else:
            # Auto-discover NPZ files
            self.samples = sorted(
                str(f.stem) for f in (self.data_dir / split).glob("*.npz")
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        sample_id = self.samples[idx]
        data = np.load(self.data_dir / self.split / f"{sample_id}.npz")

        b11 = data["b11"].astype(np.float32)
        b12 = data["b12"].astype(np.float32)
        enhancement = data["enhancement"].astype(np.float32)
        mask = data["mask"].astype(np.float32)

        # Stack input channels
        x = np.stack([b11, b12, enhancement], axis=0)

        if self.augment:
            x, mask = self._augment(x, mask)

        return {
            "input": torch.from_numpy(x),
            "mask": torch.from_numpy(mask).unsqueeze(0),
            "sample_id": sample_id,
        }

    def _augment(
        self, x: np.ndarray, mask: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Random augmentations: flips, rotations, noise."""
        # Random horizontal flip
        if np.random.random() > 0.5:
            x = np.flip(x, axis=2).copy()
            mask = np.flip(mask, axis=1).copy()

        # Random vertical flip
        if np.random.random() > 0.5:
            x = np.flip(x, axis=1).copy()
            mask = np.flip(mask, axis=0).copy()

        # Random 90° rotation
        k = np.random.randint(0, 4)
        if k > 0:
            x = np.rot90(x, k, axes=(1, 2)).copy()
            mask = np.rot90(mask, k, axes=(0, 1)).copy()

        # Gaussian noise
        if np.random.random() > 0.5:
            noise = np.random.normal(0, 0.005, x.shape).astype(np.float32)
            x = x + noise

        return x, mask


def generate_synthetic_plume(
    shape: tuple[int, int],
    center: tuple[int, int] | None = None,
    wind_direction_deg: float | None = None,
    emission_strength: float | None = None,
) -> np.ndarray:
    """Generate a synthetic Gaussian plume for data augmentation.

    Creates a plume-like enhancement pattern using a Gaussian dispersion
    model, suitable for injecting into clean S2 scenes.

    Args:
        shape: (H, W) output shape
        center: Plume source location (default: random)
        wind_direction_deg: Wind direction in degrees (default: random)
        emission_strength: Peak enhancement value (default: random 0.005-0.03)

    Returns:
        (H, W) synthetic enhancement array
    """
    h, w = shape

    if center is None:
        center = (np.random.randint(h // 4, 3 * h // 4), np.random.randint(w // 4, 3 * w // 4))

    if wind_direction_deg is None:
        wind_direction_deg = np.random.uniform(0, 360)

    if emission_strength is None:
        emission_strength = np.random.uniform(0.005, 0.03)

    # Create coordinate grid centered on source
    y, x = np.mgrid[0:h, 0:w]
    dy = y - center[0]
    dx = x - center[1]

    # Rotate to wind direction
    wind_rad = np.radians(wind_direction_deg)
    # Along-wind and cross-wind distances
    along = dx * np.cos(wind_rad) + dy * np.sin(wind_rad)
    cross = -dx * np.sin(wind_rad) + dy * np.cos(wind_rad)

    # Gaussian dispersion (Pasquill-Gifford class D)
    # σy and σz grow with downwind distance
    downwind = np.maximum(along, 0)  # Only downwind of source

    sigma_y = 0.08 * downwind + 2  # Cross-wind dispersion
    sigma_z = 0.06 * downwind + 1  # Vertical (projected)

    # Gaussian plume concentration
    with np.errstate(divide="ignore", invalid="ignore"):
        concentration = emission_strength * np.exp(-0.5 * (cross / sigma_y) ** 2)
        concentration *= np.exp(-0.5 * (downwind / (sigma_z * 3)) ** 2)
        concentration = np.where(along > 0, concentration, 0)

    # Add turbulent noise
    noise = np.random.normal(0, emission_strength * 0.1, shape)
    concentration += noise * (concentration > emission_strength * 0.01)

    return concentration.astype(np.float32)


def train_unet(
    data_dir: str | Path,
    output_dir: str | Path,
    epochs: int = 50,
    batch_size: int = 16,
    learning_rate: float = 1e-4,
) -> dict:
    """Train the U-Net plume segmentation model.

    Returns training metrics dict.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Training on device: %s", device)

    # Datasets
    train_ds = PlumeDataset(data_dir, split="train", augment=True)
    val_ds = PlumeDataset(data_dir, split="val", augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)

    # Model
    model = PlumeUNet(in_channels=3).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # Loss: combined BCE + Dice for class imbalance
    bce_loss = nn.BCELoss()

    best_val_f1 = 0.0
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            x = batch["input"].to(device)
            y = batch["mask"].to(device)

            pred = model(x)
            loss = bce_loss(pred, y) + dice_loss(pred, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        scheduler.step()
        train_loss /= len(train_loader)

        # Validate
        model.eval()
        val_tp, val_fp, val_fn = 0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                x = batch["input"].to(device)
                y = batch["mask"].to(device)

                pred = model(x)
                pred_bin = (pred > 0.5).float()

                val_tp += ((pred_bin == 1) & (y == 1)).sum().item()
                val_fp += ((pred_bin == 1) & (y == 0)).sum().item()
                val_fn += ((pred_bin == 0) & (y == 1)).sum().item()

        precision = val_tp / (val_tp + val_fp + 1e-8)
        recall = val_tp / (val_tp + val_fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)

        logger.info(
            "Epoch %d/%d — loss: %.4f, P: %.3f, R: %.3f, F1: %.3f",
            epoch + 1, epochs, train_loss, precision, recall, f1,
        )

        if f1 > best_val_f1:
            best_val_f1 = f1
            torch.save(model.state_dict(), output_path / "best_model.pth")
            logger.info("Saved best model (F1=%.3f)", f1)

    # Save final model
    torch.save(model.state_dict(), output_path / "final_model.pth")

    return {
        "best_f1": best_val_f1,
        "epochs": epochs,
        "device": str(device),
    }


def dice_loss(pred: torch.Tensor, target: torch.Tensor, smooth: float = 1.0) -> torch.Tensor:
    """Dice loss for binary segmentation."""
    pred_flat = pred.view(-1)
    target_flat = target.view(-1)
    intersection = (pred_flat * target_flat).sum()
    return 1 - (2.0 * intersection + smooth) / (pred_flat.sum() + target_flat.sum() + smooth)
