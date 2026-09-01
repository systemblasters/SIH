import torch
import torch.nn as nn
import torch.nn.functional as F
import librosa
import numpy as np
import io

# Configuration
SAMPLE_RATE = 16000
N_MELS = 128
HOP_LENGTH = 512
WIN_LENGTH = 2048
MAX_DURATION_SEC = 4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class SpectroCNN(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        # Conv block 1
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool = nn.MaxPool2d(2, 2)
        
        # Conv block 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        
        # We'll compute the flattened size dynamically in forward()
        self.fc1 = None
        self.fc2 = nn.Linear(128, num_classes)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        # x: (batch, 1, n_mels, time)
        x = self.pool(F.relu(self.bn1(self.conv1(x))))  # (B, 32, H/2, T/2)
        x = self.pool(F.relu(self.bn2(self.conv2(x))))  # (B, 64, H/4, T/4)
        
        # Flatten
        batch_size = x.size(0)
        x = x.view(batch_size, -1)  # (B, features)
        
        # Dynamically create fc1 if not already created
        if self.fc1 is None:
            num_features = x.size(1)
            self.fc1 = nn.Linear(num_features, 128).to(x.device)
            # Re-register fc1 as a module parameter
            self.fc1 = nn.Linear(num_features, 128)
            self.fc1.to(x.device)
            # Also need to re-register in module dict so parameters are tracked
            self.__dict__["fc1"] = self.fc1
        
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# Load model once
model = None

def load_model():
    global model
    if model is None:
        model = SpectroCNN().to(DEVICE)
        model.eval()
    return model

def extract_spectrogram(audio_bytes: bytes):
    """Load audio from bytes and extract log-mel spectrogram"""
    audio_file = io.BytesIO(audio_bytes)
    y, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
    
    # Truncate or pad to fixed duration
    max_samples = int(SAMPLE_RATE * MAX_DURATION_SEC)
    if len(y) > max_samples:
        y = y[:max_samples]
    else:
        y = np.pad(y, (0, max_samples - len(y)))
    
    # Extract log-mel spectrogram
    S = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_mels=N_MELS,
        hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH
    )
    # Convert to log scale
    log_S = librosa.power_to_db(S, ref=np.max)
    
    # Normalize
    log_S = (log_S - log_S.mean()) / (log_S.std() + 1e-8)
    
    # Add channel dimension: (1, n_mels, time)
    log_S = np.expand_dims(log_S, axis=0)
    
    # Convert to tensor
    tensor = torch.from_numpy(log_S).float().unsqueeze(0).to(DEVICE)
    return tensor

def predict_fake_probability(audio_bytes: bytes) -> float:
    """
    Predict probability that audio is fake.
    Returns a float between 0.0 (real) and 1.0 (fake).
    """
    model = load_model()
    spectrogram = extract_spectrogram(audio_bytes)
    
    with torch.no_grad():
        logits = model(spectrogram)
        probs = F.softmax(logits, dim=-1)
        fake_prob = probs[0, 1].item()
    
    return fake_prob

# Test block
if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python spectro_cnn_model.py <audio_file>")
        print("Example: python spectro_cnn_model.py ..\\voicesample1.mp3")
        sys.exit(0)

    audio_path = sys.argv[1]
    print(f"Analyzing: {audio_path}")

    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    audio_bytes = Path(audio_path).read_bytes()
    fake_prob = predict_fake_probability(audio_bytes)
    print(f"Fake probability: {fake_prob:.4f}")