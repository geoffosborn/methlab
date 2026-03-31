"""
CNN for daily TROPOMI plume detection.

Detects methane plumes in individual TROPOMI overpasses (without
wind rotation). Trained on the Zenodo labeled plume dataset
(3000+ labeled plumes from zenodo.org/records/8087134).

Architecture:
    - Simple CNN with 4 conv blocks + global average pooling
    - Input: single-channel CH4 anomaly patch (32×32 or 64×64)
    - Output: binary plume/no-plume probability

This complements the wind-rotation approach (Phase 2) by enabling
daily alerts on individual overpasses rather than monthly aggregates.
"""

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)


class TropomiCNN(nn.Module):
    """Lightweight CNN for TROPOMI daily plume detection."""

    def __init__(self, input_size: int = 32, in_channels: int = 1):
        super().__init__()

        self.features = nn.Sequential(
            # Block 1: 32→16
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Block 2: 16→8
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Block 3: 8→4
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # Block 4: 4→2
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (B, 1, H, W) CH4 anomaly patches

        Returns:
            (B, 1) plume probability (sigmoid)
        """
        features = self.features(x)
        logit = self.classifier(features)
        return torch.sigmoid(logit)

    def predict(self, ch4_patch: np.ndarray) -> dict:
        """Run inference on a single CH4 anomaly patch.

        Args:
            ch4_patch: (H, W) CH4 anomaly in ppb

        Returns:
            Dict with plume probability and detection flag
        """
        self.eval()
        device = next(self.parameters()).device

        x = torch.from_numpy(ch4_patch).float().unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            prob = self(x).item()

        return {
            "plume_probability": prob,
            "is_plume": prob > 0.5,
            "confidence": prob if prob > 0.5 else 1 - prob,
        }


class TropomiPlumeDataset(Dataset):
    """Dataset for TROPOMI plume detection training.

    Expected data format (Zenodo dataset):
        - Labeled CH4 anomaly patches as NPZ files
        - Each file: ch4_anomaly (32×32 or 64×64), label (0 or 1)
    """

    def __init__(self, data_dir: str | Path, split: str = "train"):
        self.data_dir = Path(data_dir) / split
        self.files = sorted(self.data_dir.glob("*.npz"))

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> dict:
        data = np.load(self.files[idx])
        ch4 = data["ch4_anomaly"].astype(np.float32)
        label = float(data["label"])

        # Normalize
        ch4 = (ch4 - ch4.mean()) / (ch4.std() + 1e-8)

        return {
            "input": torch.from_numpy(ch4).unsqueeze(0),
            "label": torch.tensor([label]),
        }


def train_tropomi_cnn(
    data_dir: str | Path,
    output_dir: str | Path,
    epochs: int = 30,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
) -> dict:
    """Train the TROPOMI plume detection CNN."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Training TROPOMI CNN on %s", device)

    train_ds = TropomiPlumeDataset(data_dir, "train")
    val_ds = TropomiPlumeDataset(data_dir, "val")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)

    model = TropomiCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.BCELoss()

    best_f1 = 0.0
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            x = batch["input"].to(device)
            y = batch["label"].to(device)

            pred = model(x)
            loss = criterion(pred, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validate
        model.eval()
        tp, fp, fn = 0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                x = batch["input"].to(device)
                y = batch["label"].to(device)

                pred = model(x)
                pred_bin = (pred > 0.5).float()
                tp += ((pred_bin == 1) & (y == 1)).sum().item()
                fp += ((pred_bin == 1) & (y == 0)).sum().item()
                fn += ((pred_bin == 0) & (y == 1)).sum().item()

        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)

        logger.info(
            "Epoch %d/%d — loss: %.4f, P: %.3f, R: %.3f, F1: %.3f",
            epoch + 1, epochs, total_loss / len(train_loader), precision, recall, f1,
        )

        if f1 > best_f1:
            best_f1 = f1
            torch.save(model.state_dict(), output_path / "best_model.pth")

    return {"best_f1": best_f1, "epochs": epochs}
