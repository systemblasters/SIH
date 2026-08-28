import os
from google import genai
from google.genai import types


def generate_report(fusion_result: dict, cues: dict) -> str:
    """
    Uses Gemini API to generate a short forensic report.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Forensic report generation failed: GEMINI_API_KEY is not set."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an AI forensics expert analyzing an audio file for a police/bank investigation.
Based on the following analysis results, write a professional forensic report (4-6 sentences) summarizing the findings.

Overall Deepfake Probability: {fusion_result['overall_probability']:.2f}
Risk Level: {fusion_result['risk_level'].upper()}
Model Scores:
- AASIST (Anti-Spoofing): {fusion_result['per_model_scores']['aasist']:.2f}
- Wav2Vec (Acoustic Features): {fusion_result['per_model_scores']['wav2vec']:.2f}
- Spectrogram CNN (Visual Audio Artifacts): {fusion_result['per_model_scores']['spectro_cnn']:.2f}

Acoustic Cues Detected:
- Pitch Variance: {cues.get('pitch_variance', 'Normal')}
- Spectral Smoothness: {cues.get('spectral_smoothness', 'Irregular')}

Your report MUST include:
1. Mention of which models contributed most heavily to the overall risk assessment.
2. A list of 2-3 specific technical reasons justifying the risk level (e.g., "low pitch variance consistent with TTS", "spectral artifacts indicative of neural codecs", or "natural breathing patterns").
3. A clear, actionable recommendation for investigators (e.g., "Treat as high-risk synthetic voice; verify identity via out-of-band channels" or "Proceed with normal verification").

Do not include any greeting or signature. Provide the concise forensic report directly.
"""
        response = client.models.generate_content(
            model="gemini-3.6-flash",  # or "gemini-1.5-flash"
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Error generating report: {str(e)}"