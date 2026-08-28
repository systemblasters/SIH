import torch
import torch.nn as nn
import torchaudio
import torchvision.models as models
import io
import librosa
import numpy as np

# Initialize the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class SpectroCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # Load a pretrained EfficientNet-B0
        # For torch < 0.13 use models.efficientnet_b0(pretrained=True)
        # For newer use models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        # Here we use the generic one which works across most recent versions
        self.efficientnet = models.efficientnet_b0(pretrained=True)
        
        # Modify the first layer to accept 1 channel instead of 3
        original_first_layer = self.efficientnet.features[0][0]
        self.efficientnet.features[0][0] = nn.Conv2d(
            1, original_first_layer.out_channels, 
            kernel_size=original_first_layer.kernel_size, 
            stride=original_first_layer.stride, 
            padding=original_first_layer.padding, 
            bias=False
        )
        
        # Modify the classifier to output 1 value (binary classification)
        num_ftrs = self.efficientnet.classifier[1].in_features
        self.efficientnet.classifier[1] = nn.Linear(num_ftrs, 1)

    def forward(self, x):
        x = self.efficientnet(x)
        return torch.sigmoid(x)

model = SpectroCNN().to(device)
model.eval()

# To load fine-tuned weights:
# model.load_state_dict(torch.load("path_to_spectro_weights.pt", map_location=device))

# Mel Spectrogram transform
mel_transform = torchaudio.transforms.MelSpectrogram(
    sample_rate=16000,
    n_mels=128,
    n_fft=1024,
    hop_length=512
).to(device)

def predict(audio_bytes: bytes) -> float:
    """
    Runs the audio through the Spectrogram CNN model.
    """
    if not audio_bytes:
        return 0.5
        
    try:
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=16000, mono=True)
        
        # Convert to tensor: (batch=1, length)
        tensor_y = torch.tensor(y, dtype=torch.float32).unsqueeze(0).to(device)
        
        with torch.no_grad():
            # Get spectrogram: (batch=1, channels=1, n_mels, time)
            spectrogram = mel_transform(tensor_y).unsqueeze(1)
            
            # Apply log scale
            log_spectrogram = torchaudio.transforms.AmplitudeToDB()(spectrogram)
            
            # Forward pass
            score = model(log_spectrogram).item()
            
        return score
    except Exception as e:
        print(f"Spectro CNN Model Error: {e}")
        return 0.5
