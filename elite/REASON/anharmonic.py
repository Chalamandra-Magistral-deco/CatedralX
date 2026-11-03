"""Projective cross-ratio features for a price series."""



def analyze(precios: list[float]) -> tuple[float, float]:
    """Return the cross-ratio and an elliptical-structure score."""
    if len(precios) < 4:
        return 0.0, 0.0

    values = [float(value) for value in precios[-4:]]
    k1, k2, k3, support = values
    denominator = (k2 - support) * (k1 - k3)
    if denominator == 0.0:
        return 0.0, 0.0

    cross_ratio = ((k1 - support) * (k2 - k3)) / denominator
    spread = max(values) - min(values)
    baseline = abs(sum(values) / len(values))
    score = 0.0 if baseline == 0.0 else min(1.0, spread / baseline)
    return float(cross_ratio), float(score)
