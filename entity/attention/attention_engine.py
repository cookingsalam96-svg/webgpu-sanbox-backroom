"""Explainable observation ranking; never changes evidence or provenance."""
from datetime import datetime, timezone


def rank_observations(observations, task=""):
    ranked = []
    for observation in observations:
        quality = observation.measurement_quality
        age_seconds = 0.0
        try:
            stamp = datetime.fromisoformat(observation.timestamp.replace("Z", "+00:00"))
            age_seconds = max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds())
        except (ValueError, TypeError):
            age_seconds = float("inf")
        quality_score = {"valid": 1.0, "degraded": 0.6, "simulated": 0.5, "unknown": 0.25, "missing": 0.0}.get(quality, 0.0)
        fresh_score = 1.0 / (1.0 + age_seconds / 60.0) if age_seconds != float("inf") else 0.0
        task_score = 1.0 if task and task.casefold() in observation.type.casefold() else 0.0
        score = 0.55 * quality_score + 0.35 * observation.confidence + 0.10 * fresh_score + 0.05 * task_score
        reason = f"quality={quality}; confidence={observation.confidence:.3f}; freshness={fresh_score:.3f}; task_match={bool(task_score)}"
        ranked.append({"observation": observation, "score": min(1.0, score), "reason": reason})
    ranked.sort(key=lambda row: row["score"], reverse=True)
    return ranked
