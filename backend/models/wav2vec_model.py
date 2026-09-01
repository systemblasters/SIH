import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

import torch
import torch.nn.functional as F
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification
import io
import librosa
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "facebook/wav2vec2-base"

# Lazy globals
_processor = None
_model = None

def _load_model():
    global _processor, _model
    if _processor is None or _model is None:
        _processor = Wav2Vec2Processor.from_pretrained(model_name)
        _model = Wav2Vec2ForSequenceClassification.from_pretrained(
            model_name, num_labels=2
        ).to(device)
        _model.eval()
    return _processor, _model

def predict(audio_bytes: bytes) -> float:
    if not audio_bytes:
        return 0.5

    try:
        processor, model = _load_model()

        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=16000, mono=True)

        inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=-1)
            fake_prob = probs[0][1].item()

        return fake_prob
    except Exception as e:
        print(f"Wav2Vec Model Error: {e}")
        return 0.5


# Test block
if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python wav2vec_model.py <audio_file>")
        print("Example: python wav2vec_model.py ..\\voicesample1.mp3")
        sys.exit(0)

    audio_path = sys.argv[1]
    print(f"Analyzing: {audio_path}")

    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    # Read file as bytes
    audio_bytes = Path(audio_path).read_bytes()

    # Call the predict function
    fake_prob = predict(audio_bytes)
    print(f"Fake probability: {fake_prob:.4f}")