"""
Embedding Generation Service
Uses sentence-transformers locally with fallback to normalized hash vector for unit tests.
"""

import logging
from typing import List
import numpy as np

from backend.app.config import get_settings

logger = logging.getLogger("lenny_growth.embeddings")
settings = get_settings()


class EmbeddingGenerator:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = 384
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence-transformers model '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers model ({e}). Falling back to deterministic embedding vector.")
            self._model = None

    def embed_text(self, text: str) -> List[float]:
        """Returns a 384-dimensional normalized float vector for text."""
        if not text:
            return [0.0] * self.dimension

        if self._model is not None:
            try:
                vector = self._model.encode(text, convert_to_numpy=True)
                # Normalize vector to unit length for cosine similarity
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                return vector.tolist()
            except Exception as e:
                logger.error(f"Error during model encoding: {e}")

        # Deterministic fallback vector generation based on character hashing
        return self._hash_vector(text)

    def _hash_vector(self, text: str) -> List[float]:
        """Generates a pseudo-random deterministic normalized 384d vector based on text."""
        seed = sum(ord(c) for c in text) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


_generator_instance = None


def get_embedding_generator() -> EmbeddingGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = EmbeddingGenerator()
    return _generator_instance
