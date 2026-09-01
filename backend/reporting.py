from typing import Dict, Any

def generate_report(analysis_data, cues):
    overall_prob = float(analysis_data.get("overall_probability", 0.5))
    risk_level = analysis_data.get("risk_level", "medium")
    scores = analysis_data.get("per_model_scores", {})

    if risk_level == "low":
        verdict = "This audio is likely real."
        interpretation = (
            "The models indicate a low probability of synthetic voice generation. "
            "The audio contains characteristics consistent with human speech."
        )
        actions = [
            "Continue with standard verification procedures.",
            "Archive this report for record-keeping."
        ]
    elif risk_level == "medium":
        verdict = "The result is inconclusive."
        interpretation = (
            "The models show mixed signals. Additional verification is recommended "
            "before trusting the speaker's identity."
        )
        actions = [
            "Verify identity through a known contact method.",
            "Cross-check relevant call, account, or transaction records."
        ]
    else:
        verdict = "This audio may contain synthetic manipulation."
        interpretation = (
            "Multiple model outputs indicate patterns associated with an "
            "AI-generated or voice-converted recording."
        )
        actions = [
            "Do not rely on the voice alone for identity verification.",
            "Verify through a trusted, independent channel.",
            "Preserve the original audio and metadata for review."
        ]

    return {
        "case_details": {
            "job_id": analysis_data.get("job_id", "N/A"),
            "timestamp": analysis_data.get("timestamp", "N/A"),
            "filename": analysis_data.get("filename", "N/A")
        },
        "risk_assessment": {
            "risk_level": risk_level.upper(),
            "deepfake_probability": round(overall_prob * 100, 1),
            "verdict": verdict
        },
        "model_results": {
            "AASIST": round(scores.get("aasist", 0.5) * 100, 1),
            "Wav2Vec 2.0": round(scores.get("wav2vec", 0.5) * 100, 1),
            "Spectro-CNN": round(scores.get("spectro_cnn", 0.5) * 100, 1)
        },
        "technical_findings": {
            "Pitch variance": cues.get("pitch_variance", "Normal"),
            "Spectral quality": cues.get("spectral_smoothness", "Natural"),
            "Breath patterns": cues.get("breath_noise", "Present")
        },
        "interpretation": interpretation,
        "recommended_actions": actions,
        "disclaimer": (
            "This is probabilistic analysis, not definitive proof. "
            "No detector is perfect. Use this result only as supporting evidence "
            "alongside other verification methods."
        )
    }