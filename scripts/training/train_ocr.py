"""
CRNN Text Recognition Training Script — Smart Traffic Violation Detection System (STVDS)
========================================================================================
Trains a custom Convolutional Recurrent Neural Network (CRNN) to recognize text on cropped 
license plate images using the dataset in `datasets/ocr/number_plate_ocr/`.

Usage:
  python train_ocr.py [--epochs 50] [--batch 32] [--lr 0.001] [--device cpu|cuda]

Weights Output:
  models/trained/ocr_best.pth
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torch.nn.functional as F

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "datasets" / "ocr" / "number_plate_ocr"
TRAINED_DIR = PROJECT_ROOT / "models" / "trained"

# Define character dictionary for OCR
# EasyOCR uses standard alphanumeric set
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "
CHAR_TO_IDX = {char: idx + 1 for idx, char in enumerate(ALPHABET)}  # CTC blank token is 0
IDX_TO_CHAR = {idx: char for char, idx in CHAR_TO_IDX.items()}
IDX_TO_CHAR[0] = "-"  # Blank token


def parse_args():
    parser = argparse.ArgumentParser(description="Train custom CRNN model for licence plate OCR.")
    parser.add_argument(
        "--epochs",
        type=int,
        default=25,
        help="Number of training epochs."
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=32,
        help="Batch size."
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
        help="Learning rate."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to train on (e.g. cpu, cuda, or auto)."
    )
    return parser.parse_args()


# ─── Data Pipeline ───────────────────────────────────────────────────────
class PlateOCRDataset(Dataset):
    """
    Loads cropped license plate images, resizes to 128x32, converts to grayscale, 
    and returns image tensor and encoded plate labels.
    """
    def __init__(self, tsv_path: Path, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.entries = []

        if not tsv_path.exists():
            print(f"  [ERROR] TSV file not found: {tsv_path}")
            return

        # Load TSV mapping
        df = pd.read_csv(tsv_path, sep="\t")
        print(f"  Found {len(df)} entries in mapping TSV.")

        # Find matching images in subdirectories (Bahrain, Ireland, Norway, USA)
        for _, row in df.iterrows():
            filename = row["filename"]
            country = row["country"]
            plate_text = str(row["plate_text"]).strip().upper()

            # Search in the country folder
            img_path = dataset_dir / country / filename
            if img_path.exists():
                self.entries.append({
                    "image_path": img_path,
                    "plate_text": plate_text
                })

        print(f"  Successfully loaded {len(self.entries)} images paired with text annotations.")

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, idx):
        entry = self.entries[idx]
        img_path = entry["image_path"]
        plate_text = entry["plate_text"]

        # Read image in grayscale
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            # Return dummy blank image on read failure
            img = np.zeros((32, 128), dtype=np.uint8)

        # Resize to standardized dimensions (128 width, 32 height)
        img = cv2.resize(img, (128, 32))
        
        # Normalize and add channel dimension: shape (1, 32, 128)
        img_tensor = torch.from_numpy(img).float() / 255.0
        img_tensor = img_tensor.unsqueeze(0)

        # Encode text labels into list of indices
        encoded = [CHAR_TO_IDX[char] for char in plate_text if char in CHAR_TO_IDX]
        label_tensor = torch.LongTensor(encoded)
        label_len = torch.IntTensor([len(encoded)])

        return img_tensor, label_tensor, label_len, plate_text


def collate_fn(batch):
    """Custom collate function to handle variable length text labels."""
    images, labels, label_lengths, raw_texts = zip(*batch)
    
    images = torch.stack(images, 0)
    # Concatenate all label tensors to a flat list for CTCLoss compatibility
    flat_labels = torch.cat(labels, 0)
    label_lengths = torch.cat(label_lengths, 0)
    
    return images, flat_labels, label_lengths, raw_texts


# ─── CRNN Architecture ──────────────────────────────────────────────────
class BidirectionalGRU(nn.Module):
    """Bidirectional GRU recurrent sequence model."""
    def __init__(self, in_features, hidden_size, out_features):
        super().__init__()
        self.rnn = nn.GRU(in_features, hidden_size, bidirectional=True, num_layers=2)
        self.fc = nn.Linear(hidden_size * 2, out_features)

    def forward(self, x):
        # Input shape: (seq_len, batch, in_features)
        x, _ = self.rnn(x)
        seq_len, batch, hidden = x.size()
        x = x.view(seq_len * batch, hidden)
        x = self.fc(x)
        x = x.view(seq_len, batch, -1)
        return x


class CRNN(nn.Module):
    """
    CRNN architecture: CNN Feature Map Extractor + Sequence GRU RNN + Linear Projection Classifier.
    Supports input size of 128x32.
    """
    def __init__(self, num_classes):
        super().__init__()
        
        # CNN: Convolutional layers for feature extraction
        self.cnn = nn.Sequential(
            # Conv1: 32x128 -> 16x64
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Conv2: 16x64 -> 8x32
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # Conv3: 8x32 -> 4x16
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            
            # Conv4: 4x16 -> 2x16 (MaxPool height only to preserve sequence length)
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),
            
            # Conv5: 2x16 -> 1x16
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            
            # Conv6: 1x16 -> 1x16
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1))  # Squeezes to 1x16
        )

        # RNN & Classifier
        # Input features: 512, Hidden features: 256, Out classes: num_classes
        self.rnn = BidirectionalGRU(in_features=512, hidden_size=256, out_features=num_classes)

    def forward(self, x):
        # Extract features
        features = self.cnn(x)
        
        # Squeeze height dimension: shape (batch, channels, height, seq_len) -> (batch, channels, seq_len)
        features = features.mean(dim=2)
        
        # Permute to shape: (seq_len, batch, channels)
        features = features.permute(2, 0, 1)
        
        # Pass through RNN sequence model
        out = self.rnn(features)
        
        return out


# ─── Training Loop ───────────────────────────────────────────────────────
def decode_prediction(pred_tensor) -> str:
    """Greedy CTC decoder to convert model predictions to readable text."""
    # pred_tensor shape: (seq_len, num_classes)
    pred_idx = torch.argmax(pred_tensor, dim=1).cpu().numpy()
    
    char_list = []
    prev_idx = 0
    for idx in pred_idx:
        if idx != 0 and idx != prev_idx:
            char_list.append(IDX_TO_CHAR[idx])
        prev_idx = idx
        
    return "".join(char_list)


def train(args):
    # Setup device
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Running on:  {device}")

    # Load dataset
    tsv_path = DATASET_DIR / "Car License Plate Detection Dataset.tsv"
    dataset = PlateOCRDataset(tsv_path, DATASET_DIR)
    
    if len(dataset) == 0:
        print("  [FATAL] Empty dataset. Cannot train OCR model.")
        sys.exit(1)

    # Split dataset into train (85%) and validation (15%)
    n_total = len(dataset)
    n_train = int(n_total * 0.85)
    train_set, val_set = torch.utils.data.random_split(
        dataset, [n_train, n_total - n_train],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(
        train_set,
        batch_size=args.batch,
        shuffle=True,
        collate_fn=collate_fn,
        drop_last=True
    )
    val_loader = DataLoader(
        val_set,
        batch_size=args.batch,
        shuffle=False,
        collate_fn=collate_fn
    )

    print(f"  Data Splits: train={len(train_set)}, val={len(val_set)}")

    # Initialize CRNN model
    # Classes: blank token (0) + alphabet characters
    num_classes = len(ALPHABET) + 1
    model = CRNN(num_classes).to(device)

    # Loss function and optimizer
    # CTC Loss expects predictions of shape (seq_len, batch, num_classes)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # Ensure output weights folder exists
    TRAINED_DIR.mkdir(parents=True, exist_ok=True)

    print("\n── Starting CRNN Training Loop ──")
    best_loss = float("inf")

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        
        for batch_idx, (images, targets, target_lengths, _) in enumerate(train_loader):
            images = images.to(device)
            targets = targets.to(device)
            target_lengths = target_lengths.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass: shape (seq_len, batch, num_classes)
            outputs = model(images)
            
            # Create input lengths tensor (seq_len for each item in batch)
            seq_len = outputs.size(0)
            input_lengths = torch.full(size=(images.size(0),), fill_value=seq_len, dtype=torch.int32).to(device)
            
            # Calculate CTC Loss
            # Log Softmax is required by PyTorch's CTCLoss
            log_probs = F.log_softmax(outputs, dim=2)
            loss = criterion(log_probs, targets, input_lengths, target_lengths)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()

        epoch_loss = train_loss / len(train_loader)
        
        # Validation Loop
        model.eval()
        val_loss = 0.0
        val_accuracy = 0
        total_chars = 0
        char_matches = 0
        
        with torch.no_grad():
            for images, targets, target_lengths, raw_texts in val_loader:
                images = images.to(device)
                targets = targets.to(device)
                target_lengths = target_lengths.to(device)
                
                outputs = model(images)
                seq_len = outputs.size(0)
                input_lengths = torch.full(size=(images.size(0),), fill_value=seq_len, dtype=torch.int32).to(device)
                
                log_probs = F.log_softmax(outputs, dim=2)
                loss = criterion(log_probs, targets, input_lengths, target_lengths)
                val_loss += loss.item()

                # Calculate string matches (spot-check accuracy)
                for idx in range(outputs.size(1)):
                    pred_str = decode_prediction(outputs[:, idx, :])
                    target_str = raw_texts[idx]
                    
                    if pred_str == target_str:
                        val_accuracy += 1
                    
                    # Levenshtein / character-level checks
                    total_chars += len(target_str)
                    char_matches += sum(1 for c1, c2 in zip(pred_str, target_str) if c1 == c2)

        val_epoch_loss = val_loss / len(val_loader)
        word_accuracy = (val_accuracy / len(val_set)) * 100
        char_accuracy = (char_matches / max(1, total_chars)) * 100

        print(f"  Epoch {epoch:02d}/{args.epochs:02d} — Train Loss: {epoch_loss:.4f} | Val Loss: {val_epoch_loss:.4f} | Word Acc: {word_accuracy:.2f}% | Char Acc: {char_accuracy:.2f}%")

        # Save weights if validation loss improved
        if val_epoch_loss < best_loss:
            best_loss = val_epoch_loss
            weights_path = TRAINED_DIR / "ocr_best.pth"
            torch.save(model.state_dict(), str(weights_path))

    # Show a sample prediction from the last epoch
    print("\n── Sample Validation Prediction ──")
    sample_img, _, _, target_text = val_set[0]
    sample_img = sample_img.unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        pred_out = model(sample_img)
        decoded = decode_prediction(pred_out[:, 0, :])
    print(f"  Ground Truth: '{target_text}'")
    print(f"  Prediction:   '{decoded}'")

    print(f"\n  ✅ Custom CRNN weights saved to: {TRAINED_DIR / 'ocr_best.pth'}")


def main():
    args = parse_args()
    print("╔══════════════════════════════════════════╗")
    print("║  CRNN Licence Plate OCR Trainer (STVDS)  ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  TSV Mapping: {DATASET_DIR / 'Car License Plate Detection Dataset.tsv'}")
    print(f"  Epochs:      {args.epochs}")
    print(f"  Batch size:  {args.batch}")
    print(f"  Learning rate:{args.lr}")

    if not DATASET_DIR.exists():
        print(f"  [FATAL] OCR dataset directory not found: {DATASET_DIR}")
        sys.exit(1)

    train(args)
    
    print("\n══════════════════════════════════════════")
    print("  OCR MODEL TRAINING COMPLETE ✓")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
