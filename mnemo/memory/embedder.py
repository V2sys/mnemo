"""
mnemo/memory/embedder.py
Owner: Vinayak

Generate semantic vectors using all-MiniLM-L6-v2 (ONNX export).
Runs on onnxruntime CPU — no PyTorch dependency.

Heavy: model loads once at startup, then encode() is fast.
"""

import logging
import numpy as np

from mnemo.config import EMBEDDING_MODEL_PATH, EMBEDDING_TOKENIZER_PATH
from mnemo.schema import EMBEDDING_DIM

log = logging.getLogger(__name__)


class Embedder:
    def __init__(self) -> None:
        self._session = None
        self._tokenizer = None

    def load(self) -> None:
        """Load the ONNX model and tokenizer. Call once at startup."""
        # TODO(week 1):
        # import onnxruntime as ort
        # from tokenizers import Tokenizer
        # self._session = ort.InferenceSession(str(EMBEDDING_MODEL_PATH))
        # self._tokenizer = Tokenizer.from_file(str(EMBEDDING_TOKENIZER_PATH))
        raise NotImplementedError("Vinayak — week 1 deliverable")

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into a normalized embedding vector.
        Returns float32 array of length EMBEDDING_DIM.
        """
        # TODO(week 1):
        # 1. Tokenize text → input_ids, attention_mask
        # 2. session.run([...]) → token embeddings
        # 3. Mean pooling using attention_mask
        # 4. L2 normalize
        # 5. Return as float32 numpy array
        raise NotImplementedError("Vinayak — week 1 deliverable")

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode multiple texts at once. Used for bulk indexing."""
        # TODO(week 2): optional but useful for first-time directory scan
        raise NotImplementedError("Vinayak — week 2 deliverable")
