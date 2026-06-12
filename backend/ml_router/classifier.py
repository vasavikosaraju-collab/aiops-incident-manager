"""
classifier.py

Thin wrapper around the trained TF-IDF + Random Forest pipeline used to
route incoming tickets to a support team.

The model is trained offline by `model_training/train_model.py` and the
resulting pipeline (vectorizer + classifier bundled together via
sklearn.pipeline.Pipeline) is saved to
`ml_router/trained_model/ticket_router.pkl`.

We load the model lazily and cache it at module level so it's only
deserialized once per process, not on every request.
"""

import functools
import logging

import joblib
from django.conf import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _load_pipeline():
    model_path = settings.ML_MODEL_PATH
    try:
        return joblib.load(model_path)
    except FileNotFoundError:
        logger.warning(
            "Ticket routing model not found at %s. "
            "Run model_training/train_model.py to generate it. "
            "Falling back to no-op routing (returns None).",
            model_path,
        )
        return None


def predict_team(description: str):
    """Predict which support team should handle a ticket.

    Returns a tuple of (team: str | None, confidence: float | None).

    `confidence` is the probability the model assigned to the predicted
    class, taken from `predict_proba`. If the model file isn't
    available (e.g. it hasn't been trained yet in a fresh checkout),
    this returns (None, None) so the ticket is simply left unrouted
    rather than raising an error.
    """

    pipeline = _load_pipeline()
    if pipeline is None or not description:
        return None, None

    prediction = pipeline.predict([description])[0]

    confidence = None
    if hasattr(pipeline, "predict_proba"):
        probabilities = pipeline.predict_proba([description])[0]
        confidence = float(max(probabilities))

    return prediction, confidence
