from typing import Dict


def fuse_scores(per_model_scores: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    """
    Fuse per-model scores into a single deepfake probability.
    
    Args:
        per_model_scores: Dict like {"aasist": 0.7, "wav2vec": 0.6, "spectro_cnn": 0.5}
        weights: Optional Dict like {"aasist": 0.4, "wav2vec": 0.4, "spectro_cnn": 0.2}
                 If None, uses equal weights.
    
    Returns:
        Fused probability between 0.0 and 1.0
    """
    if weights is None:
        # Equal weights
        weights = {k: 1.0 for k in per_model_scores}
    
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.5
    
    weighted_sum = sum(per_model_scores.get(k, 0.5) * weights.get(k, 0.0) for k in per_model_scores)
    fused_score = weighted_sum / total_weight
    
    # Clamp to [0, 1]
    fused_score = max(0.0, min(1.0, fused_score))
    
    return fused_score


def get_risk_level(prob: float) -> str:
    """
    Map probability to risk level.
    """
    if prob < 0.4:
        return "low"
    elif prob < 0.7:
        return "medium"
    else:
        return "high"


def compute_fusion(aasist_score: float, wav2vec_score: float, spectro_score: float):
    """
    Compute fused deepfake probability and risk level from 3 model scores.
    """
    per_model_scores = {
        "aasist": aasist_score,
        "wav2vec": wav2vec_score,
        "spectro_cnn": spectro_score
    }
    
    # Use fuse_scores for weighted/average fusion
    overall_probability = fuse_scores(per_model_scores)
    
    # Get risk level
    risk_level = get_risk_level(overall_probability)
    
    # Return as an object with .model_dump() support
    class FusionResult:
        def __init__(self, overall_probability, risk_level, per_model_scores):
            self.overall_probability = overall_probability
            self.risk_level = risk_level
            self.per_model_scores = per_model_scores
        
        def model_dump(self):
            return {
                "overall_probability": self.overall_probability,
                "risk_level": self.risk_level,
                "per_model_scores": self.per_model_scores
            }
    
    return FusionResult(overall_probability, risk_level, per_model_scores)