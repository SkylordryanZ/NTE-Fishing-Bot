"""
benchmark.py — Hardware performance tester for NTE Fishing.
Runs 5 epochs of training for multiple configurations to find the fastest setup.
"""
import time
import os
import torch
from train import FishingDataset, TARGET_CLASSES, IMG_SIZE, LR, TRAINING_DATA_DIR
from torchvision import models, transforms
from torch.utils.data import DataLoader, random_split, WeightedRandomSampler
import torch.nn as nn
import torch.optim as optim
import numpy as np

def run_bench(batch_size, num_workers):
    device_type = os.environ.get("TRAIN_DEVICE", "dml").lower()
    if device_type == "cuda":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        import torch_directml
        device = torch_directml.device()

    train_tfm = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    
    full_ds = FishingDataset(TRAINING_DATA_DIR, TARGET_CLASSES, transform=train_tfm)
    n_train = int(len(full_ds) * 0.8)
    n_val = len(full_ds) - n_train
    train_ds, _ = random_split(full_ds, [n_train, n_val])
    
    # Weighted sampler
    train_targets = [full_ds.targets[i] for i in train_ds.indices]
    class_counts = np.bincount(train_targets).astype(float)
    class_weights = 1.0 / (class_counts + 1e-6)
    sample_w = [class_weights[t] for t in train_targets]
    sampler = WeightedRandomSampler(sample_w, len(sample_w))

    loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, 
                        num_workers=num_workers, pin_memory=True)
    
    model = models.mobilenet_v2(num_classes=len(full_ds.classes)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)

    print(f"\n[Bench] Testing BS={batch_size}, Workers={num_workers}...")
    
    # Warmup
    model.train()
    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        model(imgs)
        break

    start_time = time.time()
    for epoch in range(5):
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5
    print(f"        Average time per epoch: {avg_time:.3f}s")
    return avg_time

if __name__ == "__main__":
    configs = []
    for bs in [4, 8, 16, 32]:
        for nw in [0, 1, 2]:
            configs.append((bs, nw))
    
    results = []
    print("=== NTE Fishing Hardware Benchmark ===")
    print("Running 5 epochs per config...")
    
    for bs, nw in configs:
        try:
            t = run_bench(bs, nw)
            results.append((bs, nw, t))
        except Exception as e:
            print(f"      [FAILED] {e}")

    import json
    
    print("\n" + "="*40)
    print("FINAL RESULTS (Lower is better)")
    print("="*40)
    sorted_results = sorted(results, key=lambda x: x[2])
    for bs, nw, t in sorted_results:
        print(f"BS: {bs:2d} | Workers: {nw} | Time: {t:.3f}s")
    print("="*40)
    
    if sorted_results:
        best_bs, best_nw, _ = sorted_results[0]
        config_path = os.path.join(os.path.dirname(__file__), "training_config.json")
        try:
            with open(config_path, "w") as f:
                json.dump({"BATCH_SIZE": best_bs, "NUM_WORKERS": best_nw}, f, indent=4)
            print(f"\n[Success] Automatically saved best config to training_config.json!")
            print(f"          train.py will now use BS={best_bs} and Workers={best_nw}")
        except Exception as e:
            print(f"\n[Warning] Failed to save optimal config: {e}")

