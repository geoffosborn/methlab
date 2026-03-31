"""
EfficientNet-based plume/flare/negative classifier with Grad-CAM.

Classifies S2 scene patches into:
    - plume: methane plume detected
    - flare: gas flaring (bright thermal anomaly, not methane)
    - negative: no detection (cloud, terrain, noise)

Grad-CAM provides interpretability by highlighting which image regions
drove the classification decision.

Reference:
    Selvaraju et al. (2017) — "Grad-CAM: Visual Explanations from
    Deep Networks via Gradient-based Localization"
"""

import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

logger = logging.getLogger(__name__)

CLASS_NAMES = ["negative", "plume", "flare"]
NUM_CLASSES = len(CLASS_NAMES)


class PlumeClassifier(nn.Module):
    """EfficientNet-B0 classifier for plume/flare/negative detection."""

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        in_channels: int = 3,
        model_name: str = "efficientnet_b0",
    ):
        super().__init__()
        self.backbone = timm.create_model(
            model_name,
            pretrained=True,
            in_chans=in_channels,
            num_classes=num_classes,
        )
        self._gradients = None
        self._activations = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning class logits."""
        return self.backbone(x)

    def predict(self, patch: np.ndarray) -> dict:
        """Run inference on a single patch.

        Args:
            patch: (C, H, W) numpy array

        Returns:
            Dict with class probabilities and predicted class
        """
        self.eval()
        device = next(self.parameters()).device

        x = torch.from_numpy(patch).float().unsqueeze(0).to(device)

        with torch.no_grad():
            logits = self(x)
            probs = F.softmax(logits, dim=1).squeeze().cpu().numpy()

        pred_idx = int(np.argmax(probs))

        return {
            "predicted_class": CLASS_NAMES[pred_idx],
            "confidence": float(probs[pred_idx]),
            "probabilities": {
                name: float(probs[i]) for i, name in enumerate(CLASS_NAMES)
            },
        }

    def predict_with_gradcam(
        self, patch: np.ndarray, target_class: int | None = None
    ) -> dict:
        """Run inference with Grad-CAM visualization.

        Args:
            patch: (C, H, W) numpy array
            target_class: Class index for Grad-CAM (default: predicted class)

        Returns:
            Dict with predictions and Grad-CAM heatmap
        """
        self.eval()
        device = next(self.parameters()).device

        x = torch.from_numpy(patch).float().unsqueeze(0).to(device)
        x.requires_grad_(True)

        # Register hooks on the last conv layer
        target_layer = self._get_last_conv_layer()

        activations = []
        gradients = []

        def forward_hook(module, input, output):
            activations.append(output)

        def backward_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0])

        fwd_handle = target_layer.register_forward_hook(forward_hook)
        bwd_handle = target_layer.register_full_backward_hook(backward_hook)

        # Forward pass
        logits = self(x)
        probs = F.softmax(logits, dim=1).squeeze()

        if target_class is None:
            target_class = int(torch.argmax(probs))

        # Backward pass for target class
        self.zero_grad()
        logits[0, target_class].backward()

        # Compute Grad-CAM
        grads = gradients[0].squeeze()  # (C, H, W)
        acts = activations[0].squeeze()  # (C, H, W)

        weights = grads.mean(dim=(1, 2))  # Global average pooling of gradients
        cam = torch.zeros(acts.shape[1:], device=device)
        for i, w in enumerate(weights):
            cam += w * acts[i]

        cam = F.relu(cam)  # Only positive contributions
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        # Resize to input dimensions
        cam = F.interpolate(
            cam.unsqueeze(0).unsqueeze(0),
            size=patch.shape[1:],
            mode="bilinear",
            align_corners=False,
        ).squeeze()

        # Cleanup hooks
        fwd_handle.remove()
        bwd_handle.remove()

        return {
            "predicted_class": CLASS_NAMES[int(torch.argmax(probs))],
            "confidence": float(probs[int(torch.argmax(probs))].item()),
            "probabilities": {
                name: float(probs[i].item()) for i, name in enumerate(CLASS_NAMES)
            },
            "gradcam": cam.detach().cpu().numpy(),
            "target_class": CLASS_NAMES[target_class],
        }

    def _get_last_conv_layer(self) -> nn.Module:
        """Get the last convolutional layer for Grad-CAM."""
        # EfficientNet: last conv in the final block
        for name, module in reversed(list(self.backbone.named_modules())):
            if isinstance(module, nn.Conv2d):
                return module
        raise ValueError("No Conv2d layer found")


def train_classifier(
    data_dir: str | Path,
    output_dir: str | Path,
    epochs: int = 30,
    batch_size: int = 32,
    learning_rate: float = 3e-4,
) -> dict:
    """Train the plume classifier.

    Expects data_dir to contain train/ and val/ subdirectories with
    class-labeled NPZ files or image folders.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = PlumeClassifier().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss()

    # Training loop follows standard PyTorch pattern
    # (Dataset/DataLoader setup omitted — depends on data format)

    logger.info(
        "Classifier training configured: %s, %d epochs, lr=%.1e",
        device, epochs, learning_rate,
    )

    return {"status": "configured", "device": str(device), "epochs": epochs}
