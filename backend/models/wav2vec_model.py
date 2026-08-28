import torch
import torch.nn.functional as F
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification
import io
import librosa
import numpy as np

# Initialize the model and processor
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "facebook/wav2vec2-base"
processor = Wav2Vec2Processor.from_pretrained(model_name)
# We load the base model with a sequence classification head for 2 classes (real vs fake)
# This will initialize the classification head with random weights until fine-tuned
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name, num_labels=2).to(device)
model.eval()

def predict(audio_bytes: bytes) -> float:
    """
    Runs the audio through the Wav2Vec2 classification model.
    """
    if not audio_bytes:
        return 0.5
        
    try:
        # Load audio
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=16000, mono=True)
        
        # Process input values
        inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            logits = model(**inputs).logits
            # Apply softmax to get probabilities
            probs = F.softmax(logits, dim=-1)
            # Assuming class 1 is "fake"
            fake_prob = probs[0][1].item()
            
        return fake_prob
    except Exception as e:
        print(f"Wav2Vec Model Error: {e}")
        return 0.5
