# SIH 104 - Deepfake Voice Detection

This project is a full-stack application built for the Smart India Hackathon (SIH) 2026, targeting Problem Statement 104: AI-Powered Real-Time Detection and Prevention of AI-generated (deepfake) voices for banks and police.

## Features
- **FastAPI Backend**: Provides endpoints for file upload and real-time WebSocket analysis.
- **Next.js Frontend**: A modern, clean UI for investigators to upload audio files and view analysis results in real-time.
- **Dummy Deepfake Models**: Placeholder logic for AASIST, Wav2Vec 2.0, and Spectrogram CNN algorithms.
- **Forensic Reporting**: Integrates with Google's Gemini API to generate concise forensic reports based on the analysis.

## Prerequisites
- Docker & Docker Compose
- Node.js 20 (if running frontend locally outside Docker)
- Python 3.11 (if running backend locally outside Docker)
- A Gemini API Key (`GEMINI_API_KEY`)

## Setup Instructions

1. **Clone the repository** (or use the provided workspace).
2. **Set Environment Variables**:
   Export your Gemini API key in your terminal before running docker-compose:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   # On Windows PowerShell:
   # $env:GEMINI_API_KEY="your_api_key_here"
   ```
3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
4. **Access the Application**:
   - Frontend UI: http://localhost:3000
   - Backend API Docs: http://localhost:8000/docs

## Replacing Dummy Models
The models in `backend/models/` currently use simple hashing functions to simulate probability scores. To integrate real deepfake detection algorithms:
1. Replace the logic in `backend/models/aasist_model.py`, `wav2vec_model.py`, and `spectro_cnn_model.py`.
2. Load your PyTorch or TensorFlow model weights during application startup.
3. Update the `predict()` function to preprocess the audio bytes and pass them through your actual neural networks.
