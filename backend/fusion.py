from pydantic import BaseModel
from typing import Dict, Any

class FusionResult(BaseModel):
    overall_probability: float
    risk_level: str
    per_model_scores: Dict[str, float]

def compute_fusion(aasist_score: float, wav2vec_score: float, spectro_score: float) -> FusionResult:
    """
    Computes a weighted average of the model scores.
    Currently uses equal weights.
    """
    # Until Wav2Vec and Spectro-CNN receive real trained weights,
    # AASIST is the only trustworthy detector in the ensemble.
    overall_prob = (
        0.90 * aasist_score
        + 0.05 * wav2vec_score
        + 0.05 * spectro_score
    )
    
    # Determine risk level
    if overall_prob < 0.4:
        risk_level = "low"
    elif overall_prob < 0.7:
        risk_level = "medium"
    else:
        risk_level = "high"
        
    return FusionResult(
        overall_probability=overall_prob,
        risk_level=risk_level,
        per_model_scores={
            "aasist": aasist_score,
            "wav2vec": wav2vec_score,
            "spectro_cnn": spectro_score
        }
    )
