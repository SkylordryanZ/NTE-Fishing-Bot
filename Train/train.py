"""
train.py — 2-Phase MobileNetV2 trainer for NTE Fishing state detection.

Phase 1 (Head Warmup):   Backbone frozen,  trains only the classifier.  Fast & stable.
Phase 2 (Fine-Tuning):   Backbone unfrozen, trains everything at low LR. Pushes to peak.

Both phases use early stopping so training stops the moment it stops improving,
regardless of the epoch limit.

Output:
    model/state_classifier.onnx   — best model across both phases
    model/classes.json            — class index → name mapping
"""

import os
import sys
import json
import copy
import datetime
import shutil

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, random_split
from torchvision import models, transforms, datasets
from PIL import Image

# ------------------------------------------------------------------ #
# Device                                                               #
# ------------------------------------------------------------------ #
DEVICE = None  # Set in main()

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #
_ROOT             = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_DIR = os.path.join(_ROOT, "TrainingData")
# Model directory is at the project root
MODEL_DIR         = os.path.join(_ROOT, "..", "model")
ONNX_PATH         = os.path.join(MODEL_DIR, "state_classifier.onnx")
CLASSES_PATH      = os.path.join(MODEL_DIR, "classes.json")

IMG_SIZE    = 224
BATCH_SIZE  = 16
NUM_WORKERS = 0

# --- Phase 1: Head only ---
P1_EPOCHS   = 15      # Max epochs (early stopping will usually kick in sooner)
P1_LR       = 3e-4
P1_PATIENCE = 5       # Stop if no improvement for 5 epochs

# --- Phase 2: Full fine-tune ---
P2_EPOCHS   = 25      # Max epochs
P2_LR       = 5e-5    # Very low LR to avoid destroying pretrained features
P2_PATIENCE = 7       # More patience since improvement is slower

TARGET_CLASSES = {"CAUGHT", "HOOKED", "IDLE", "MINIGAME", "WAITING"}


# ------------------------------------------------------------------ #
# Corrupted Image Quarantine                                           #
# ------------------------------------------------------------------ #
def scan_and_quarantine(data_dir):
    """Scan all images in data_dir subfolders. Move corrupted ones to CORRUPTED/."""
    corrupted_dir = os.path.join(data_dir, "CORRUPTED")
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".ppm", ".tif", ".tiff"}
    total_scanned = 0
    total_corrupted = 0

    print("\n[Scan] Checking all images for corruption...")
    for cls_folder in os.listdir(data_dir):
        if cls_folder == "CORRUPTED":
            continue
        folder_path = os.path.join(data_dir, cls_folder)
        if not os.path.isdir(folder_path):
            continue
        for fname in os.listdir(folder_path):
            if os.path.splitext(fname)[1].lower() not in valid_exts:
                continue
            fpath = os.path.join(folder_path, fname)
            total_scanned += 1
            try:
                with Image.open(fpath) as img:
                    img.verify()
            except Exception:
                dest_dir = os.path.join(corrupted_dir, cls_folder)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.move(fpath, os.path.join(dest_dir, fname))
                total_corrupted += 1
                print(f"  [!] Corrupted → moved: {cls_folder}/{fname}")

    if total_corrupted == 0:
        print(f"[Scan] ✅ All {total_scanned} images are clean!")
    else:
        print(f"[Scan] ⚠️  Moved {total_corrupted}/{total_scanned} corrupted images to CORRUPTED/ folder.")
    print()


# ------------------------------------------------------------------ #
# Filtered dataset                                                      #
# ------------------------------------------------------------------ #
class FishingDataset(datasets.ImageFolder):
    """ImageFolder that only loads TARGET_CLASSES and remaps labels to 0..N-1."""

    def __init__(self, root, target_classes, transform=None):
        super().__init__(root, transform=transform)

        keep_orig_idx = {
            self.class_to_idx[c]
            for c in target_classes
            if c in self.class_to_idx
        }

        self.samples = [(p, l) for p, l in self.samples if l in keep_orig_idx]
        self.targets = [l for _, l in self.samples]

        sorted_orig = sorted(keep_orig_idx)
        old_to_new  = {old: new for new, old in enumerate(sorted_orig)}

        self.samples = [(p, old_to_new[l]) for p, l in self.samples]
        self.targets = [old_to_new[l] for l in self.targets]

        self.classes      = [c for c in self.classes if c in target_classes]
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}


# ------------------------------------------------------------------ #
# Training Phase Runner                                                #
# ------------------------------------------------------------------ #
def run_phase(phase_num, model, train_loader, val_loader,
              epochs, lr, patience, criterion, device):
    """
    Run one training phase with early stopping and gradient clipping.
    Returns (best_val_acc, best_state_dict).
    """
    label = "HEAD WARMUP" if phase_num == 1 else "FULL FINE-TUNE"
    print(f"\n{'='*55}")
    print(f"  PHASE {phase_num}: {label}")
    print(f"  Max epochs: {epochs}  |  LR: {lr}  |  Patience: {patience}")
    print(f"{'='*55}\n")

    # Optimise only parameters that require grad
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable, lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=lr * 0.01)

    best_val_acc   = 0.0
    best_weights   = copy.deepcopy(model.state_dict())
    epochs_no_gain = 0

    for epoch in range(1, epochs + 1):
        # --- Train ---
        model.train()
        total_loss = 0.0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), labels)
            loss.backward()
            # Gradient clipping prevents exploding gradients during fine-tune
            torch.nn.utils.clip_grad_norm_(trainable, max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        # --- Validate ---
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                preds   = model(imgs).argmax(dim=1)
                correct += (preds == labels).sum().item()
                total   += labels.size(0)

        val_acc = correct / total if total > 0 else 0.0
        scheduler.step()

        improved = val_acc > best_val_acc
        marker   = " ✅" if improved else ""
        if improved:
            best_val_acc   = val_acc
            best_weights   = copy.deepcopy(model.state_dict())
            epochs_no_gain = 0
        else:
            epochs_no_gain += 1

        print(f"  P{phase_num} Epoch {epoch:3d}/{epochs}"
              f"  |  Loss: {total_loss / len(train_loader):.4f}"
              f"  |  Val: {val_acc:.1%}"
              f"  |  Best: {best_val_acc:.1%}"
              f"  |  No-gain: {epochs_no_gain}/{patience}"
              f"{marker}")

        if epochs_no_gain >= patience:
            print(f"\n  [Early Stop] No improvement for {patience} epochs. Stopping phase {phase_num}.")
            break

    print(f"\n  Phase {phase_num} complete. Best val accuracy: {best_val_acc:.1%}")
    return best_val_acc, best_weights


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #
def main():
    global DEVICE, BATCH_SIZE, NUM_WORKERS

    # Load hardware config (inside main so DataLoader workers don't reprint)
    _config_file = os.path.join(_ROOT, "training_config.json")
    if os.path.exists(_config_file):
        try:
            with open(_config_file, "r") as f:
                _opt = json.load(f)
                BATCH_SIZE  = _opt.get("BATCH_SIZE", BATCH_SIZE)
                NUM_WORKERS = _opt.get("NUM_WORKERS", NUM_WORKERS)
                print(f"[Config] Loaded hardware settings: BS={BATCH_SIZE}, Workers={NUM_WORKERS}")
        except Exception as e:
            print(f"[Config] Warning: Failed to load training_config.json: {e}")

    device_type = os.environ.get("TRAIN_DEVICE", "dml").lower()
    if device_type == "cuda":
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Train] ✅ Device: {DEVICE} (CUDA/NVIDIA)")
    else:
        import torch_directml
        DEVICE = torch_directml.device()
        print(f"[Train] ✅ Device: {DEVICE} (DirectML/AMD)")

    os.makedirs(MODEL_DIR, exist_ok=True)

    # ---- Quarantine corrupted images ----
    scan_and_quarantine(TRAINING_DATA_DIR)

    # ---- Transforms ----
    train_tfm = transforms.Compose([
        transforms.Resize((IMG_SIZE + 40, IMG_SIZE + 40)),
        transforms.RandomCrop(IMG_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.4, hue=0.05),
        transforms.RandomRotation(15),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tfm = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # ---- Filter available classes ----
    VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.ppm', '.tif', '.tiff'}
    available_classes = set()
    for cls in TARGET_CLASSES:
        folder = os.path.join(TRAINING_DATA_DIR, cls)
        if os.path.isdir(folder):
            has_images = any(
                os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
                for f in os.listdir(folder)
            )
            if has_images:
                available_classes.add(cls)
            else:
                print(f"[Train] ⚠️  Skipping '{cls}' — folder is empty")
        else:
            print(f"[Train] ⚠️  Skipping '{cls}' — folder not found")

    if not available_classes:
        print("[Train] ❌ No images found! Add labelled images first.")
        print("[Train] Expected folders: " + str(TARGET_CLASSES))
        print("[Train] Searched in: " + TRAINING_DATA_DIR)
        sys.exit(1)

    # ---- Dataset ----
    full_ds = FishingDataset(TRAINING_DATA_DIR, available_classes, transform=train_tfm)
    if len(full_ds) == 0:
        print("[Train] ❌ No images found in TrainingData!")
        sys.exit(1)

    classes     = full_ds.classes
    num_classes = len(classes)

    print(f"\n[Train] Classes ({num_classes}): {classes}")
    for cls in classes:
        count = full_ds.targets.count(full_ds.class_to_idx[cls])
        print(f"  {cls:12s}: {count:4d} images")

    with open(CLASSES_PATH, "w") as f:
        json.dump(classes, f, indent=2)
    print(f"[Train] Class map → {CLASSES_PATH}")

    # ---- Train / Val split ----
    n_val   = max(1, int(len(full_ds) * 0.2))
    n_train = len(full_ds) - n_val
    train_ds, val_ds = random_split(full_ds, [n_train, n_val],
                                    generator=torch.Generator().manual_seed(42))

    val_ds_copy = copy.copy(full_ds)
    val_ds_copy.transform = val_tfm
    val_ds_copy.samples   = [full_ds.samples[i] for i in val_ds.indices]
    val_ds_copy.targets   = [full_ds.targets[i]  for i in val_ds.indices]

    # ---- Weighted sampler (handles class imbalance) ----
    train_targets = [full_ds.targets[i] for i in train_ds.indices]
    class_counts  = np.bincount(train_targets, minlength=num_classes).astype(float)
    class_weights = 1.0 / (class_counts + 1e-6)
    sample_w      = [class_weights[t] for t in train_targets]
    sampler       = WeightedRandomSampler(sample_w, len(sample_w), replacement=True)

    train_loader = DataLoader(train_ds,    batch_size=BATCH_SIZE, sampler=sampler, num_workers=NUM_WORKERS)
    val_loader   = DataLoader(val_ds_copy, batch_size=BATCH_SIZE, shuffle=False,   num_workers=NUM_WORKERS)

    print(f"\n[Train] {n_train} training samples | {n_val} validation samples")

    # ---- Model: MobileNetV2 with pretrained backbone ----
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier = nn.Sequential(
        nn.Dropout(0.4),
        nn.Linear(model.last_channel, num_classes),
    )

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # ================================================================ #
    # PHASE 1 — Freeze backbone, train head only                       #
    # ================================================================ #
    for param in model.features.parameters():
        param.requires_grad = False
    model = model.to(DEVICE)

    p1_acc, p1_weights = run_phase(
        1, model, train_loader, val_loader,
        P1_EPOCHS, P1_LR, P1_PATIENCE, criterion, DEVICE
    )

    # Load best weights from Phase 1 before entering Phase 2
    model.load_state_dict(p1_weights)

    # ================================================================ #
    # PHASE 2 — Unfreeze all layers, fine-tune at low LR               #
    # ================================================================ #
    for param in model.features.parameters():
        param.requires_grad = True

    p2_acc, p2_weights = run_phase(
        2, model, train_loader, val_loader,
        P2_EPOCHS, P2_LR, P2_PATIENCE, criterion, DEVICE
    )

    # Pick the best weights across both phases
    if p2_acc >= p1_acc:
        best_weights = p2_weights
        best_acc     = p2_acc
        print(f"\n[Train] Phase 2 won: {p2_acc:.1%} vs Phase 1: {p1_acc:.1%}")
    else:
        best_weights = p1_weights
        best_acc     = p1_acc
        print(f"\n[Train] Phase 1 was better: {p1_acc:.1%} vs Phase 2: {p2_acc:.1%}")

    # ---- Archive old model ----
    if os.path.exists(ONNX_PATH):
        archive_dir = os.path.join(MODEL_DIR, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        timestamp    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(archive_dir, f"state_classifier_{timestamp}.onnx")
        shutil.copy2(ONNX_PATH, archive_path)
        print(f"[Train] Archived old model → {archive_path}")

    # ---- Export best model to ONNX ----
    model.load_state_dict(best_weights)
    model.eval()
    model.to("cpu")  # Always export from CPU for portability

    dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
    torch.onnx.export(
        model, dummy, ONNX_PATH,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"\n[Train] ✅ Final model accuracy: {best_acc:.1%}")
    print(f"[Train] Model saved → {ONNX_PATH}")
    print(f"[Train] Classes:       {classes}")
    print("[Train] Run run.bat to use the AI bot!")


if __name__ == "__main__":
    main()
