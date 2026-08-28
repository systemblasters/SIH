import io
import json
import os
import sys

import librosa
import numpy as np
import torch


# Docker will copy the official AASIST repository here.
AASIST_REPO_PATH = "/app/aasist"

# Useful only if you execute backend code directly on Windows without Docker.
WINDOWS_AASIST_REPO_PATH = r"C:\Users\Asjad\SIH\aasist"

if os.path.isdir(AASIST_REPO_PATH):
    sys.path.insert(0, AASIST_REPO_PATH)
elif os.path.isdir(WINDOWS_AASIST_REPO_PATH):
    sys.path.insert(0, WINDOWS_AASIST_REPO_PATH)
else:
    raise RuntimeError(
        "Official AASIST repository was not found. "
        "Expected /app/aasist in Docker or C:\\Users\\Asjad\\SIH\\aasist on Windows."
    )

# Official model from clovaai/aasist/models/AASIST.py
from models.AASIST import Model

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_PATH = os.path.join(BASE_DIR, "weights", "AASIST.pth")
CONFIG_PATH = os.path.join(BASE_DIR, "weights", "AASIST.conf")

SAMPLE_RATE = 16000
TARGET_LENGTH = 64600


def _load_model() -> torch.nn.Module:
    """Load the official AASIST architecture and its matching checkpoint."""
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError(f"AASIST config not found: {CONFIG_PATH}")

    if not os.path.isfile(WEIGHTS_PATH):
        raise FileNotFoundError(f"AASIST weights not found: {WEIGHTS_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    model_config = config["model_config"]
    model = Model(model_config).to(device)

    checkpoint = torch.load(WEIGHTS_PATH, map_location=device)

    # Official checkpoints may be a state_dict directly or nested in a dict.
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        checkpoint = checkpoint["model_state_dict"]
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        checkpoint = checkpoint["state_dict"]

    # Remove DataParallel prefix when present.
    if isinstance(checkpoint, dict):
        checkpoint = {
            key.replace("module.", "", 1): value
            for key, value in checkpoint.items()
        }

    model.load_state_dict(checkpoint, strict=True)
    model.eval()
    print(f"AASIST loaded successfully on {device}: {WEIGHTS_PATH}")
    return model


try:
    model = _load_model()
    MODEL_READY = True
except Exception as error:
    model = None
    MODEL_READY = False
    print(f"ERROR: AASIST was not loaded. {error}")


def _fix_audio_length(audio: np.ndarray) -> np.ndarray:
    """
    Official AASIST config expects exactly 64,600 samples.
    For short audio: repeat it.
    For long audio: use the first 64,600 samples.
    """
    if len(audio) == 0:
        return np.zeros(TARGET_LENGTH, dtype=np.float32)

    if len(audio) < TARGET_LENGTH:
        repeat_count = int(np.ceil(TARGET_LENGTH / len(audio)))
        audio = np.tile(audio, repeat_count)

    return audio[:TARGET_LENGTH].astype(np.float32)


def predict(audio_bytes: bytes) -> float:
    """
    Returns fake/deepfake probability in [0, 1].

    AASIST outputs two class logits:
    index 0 = bona fide / real
    index 1 = spoof / fake.
    We use softmax and return class-1 probability.
    """
    if not audio_bytes:
        return 0.5

    if not MODEL_READY or model is None:
        print("AASIST unavailable; returning neutral score 0.5.")
        return 0.5

    try:
        waveform, _ = librosa.load(
            io.BytesIO(audio_bytes),
            sr=SAMPLE_RATE,
            mono=True
        )

        waveform = _fix_audio_length(waveform)
        input_tensor = torch.from_numpy(waveform).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model(input_tensor)

            # Official AASIST implementations return logits directly,
            # but handle a tuple defensively.
            if isinstance(logits, tuple):
                logits = logits[-1]

            probabilities = torch.softmax(logits, dim=1)
            fake_probability = probabilities[0, 1].item()

        return float(np.clip(fake_probability, 0.0, 1.0))

    except Exception as error:
        print(f"AASIST inference error: {error}")
        return 0.5