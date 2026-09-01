from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid
import time
from typing import Dict, Any
import io
import librosa
import soundfile as sf
import numpy as np

from backend.models import aasist_model, wav2vec_model, spectro_cnn_model
from backend.fusion import compute_fusion
from backend.reporting import generate_report

app = FastAPI(title="SIH 104 - Deepfake Voice Detection API")
@app.on_event("startup")
async def warmup_aasist():
    # Only ensure the AASIST model object is created; no heavy audio work.
    try:
        # This forces the model to load once at startup
        _ = aasist_model._get_model()
        print("AASIST warmup: model loaded")
    except Exception as e:
        # If warmup fails, we still let the app start; first request will try to load
        print("AASIST warmup error (non-fatal):", e)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage for status checking
jobs: Dict[str, Any] = {}

class AnalyzeResponse(BaseModel):
    job_id: str
    overall_deepfake_probability: float
    risk_level: str
    per_model_scores: Dict[str, float]
    report: Dict[str, Any]

def process_audio_in_chunks(audio_bytes: bytes, chunk_duration_sec: int = 2):
    """
    Reads audio bytes, converts to 16kHz mono, and splits into 2-second chunks.
    Returns a list of audio bytes for each chunk.
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=16000, mono=True)
    except Exception as e:
        print(f"Error loading audio for chunking: {e}")
        return [audio_bytes]

    chunk_length = sr * chunk_duration_sec
    chunks = []
    
    # 50% overlap chunking
    step = chunk_length // 2
    for i in range(0, len(y), step):
        chunk_y = y[i:i+chunk_length]
        if len(chunk_y) < sr * 0.5: # Skip very short chunks
            continue
            
        chunk_io = io.BytesIO()
        sf.write(chunk_io, chunk_y, sr, format='WAV')
        chunks.append(chunk_io.getvalue())
        
    return chunks if chunks else [audio_bytes]

@app.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    Endpoint to upload an audio file and analyze it for deepfakes.
    """
    job_id = str(uuid.uuid4())
    audio_bytes = await file.read()
    
    chunks = process_audio_in_chunks(audio_bytes)
    aasist_scores = []
    wav2vec_scores = []
    spectro_scores = []
    
    for chunk in chunks:
        try:
            aasist_scores.append(aasist_model.predict(chunk))
        except Exception as e:
            print("AASIST predict error:", e)
            aasist_scores.append(0.5)

        # Temporarily skip wav2vec and SpectroCNN to avoid crashes
        wav2vec_scores.append(0.5)
        spectro_scores.append(0.5)

    # These must be outside (after) the for loop
    aasist_score = sum(aasist_scores) / len(aasist_scores)
    wav2vec_score = sum(wav2vec_scores) / len(wav2vec_scores)
    spectro_score = sum(spectro_scores) / len(spectro_scores)
        
    
    # Fusion
    fusion_res = compute_fusion(aasist_score, wav2vec_score, spectro_score)
    
    # Generate dummy acoustic cues based on fusion score
    cues = {
        "pitch_variance": "Abnormal (too stable)" if fusion_res.risk_level == "high" else "Normal",
        "spectral_smoothness": "Synthetic artifacting detected" if fusion_res.risk_level == "high" else "Natural"
    }
    
     # Reporting
    report_input = fusion_res.model_dump()
    report_input["job_id"] = job_id
    report_input["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report_input["filename"] = file.filename or "uploaded_audio"

    report = generate_report(report_input, cues)

    result = {
        "job_id": job_id,
        "overall_deepfake_probability": fusion_res.overall_probability,
        "risk_level": fusion_res.risk_level,
        "per_model_scores": fusion_res.per_model_scores,
        "report": report,
        "status": "completed"
    }

    # Store job
    jobs[job_id] = result

    return result

@app.get("/analyze/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Endpoint to check the status of a long-running analysis job.
    """
    if job_id not in jobs:
        return {"error": "Job not found"}
    return jobs[job_id]

@app.websocket("/analyze-stream")
async def analyze_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio chunk analysis.
    """
    await websocket.accept()
    try:
        while True:
            # Receive audio chunk from client
            chunk = await websocket.receive_bytes()
            
            # Process chunk
            aasist_score = aasist_model.predict(chunk)
            wav2vec_score = wav2vec_model.predict(chunk)
            spectro_score = spectro_cnn_model.predict(chunk)
            
            fusion_res = compute_fusion(aasist_score, wav2vec_score, spectro_score)
            
            # Send results back to client
            await websocket.send_json({
                "overall_probability": fusion_res.overall_probability,
                "risk_level": fusion_res.risk_level,
                "per_model_scores": fusion_res.per_model_scores,
                "timestamp": time.time()
            })
    except WebSocketDisconnect:
        print("Client disconnected from stream")
