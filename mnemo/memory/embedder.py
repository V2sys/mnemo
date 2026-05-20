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
        if not EMBEDDING_MODEL_PATH.exists() or not EMBEDDING_TOKENIZER_PATH.exists():
            raise FileNotFoundError(
                f"Embedding models not found at {EMBEDDING_MODEL_PATH}. "
                "Please refer to docs/setup.md to download them."
            )
            
        import onnxruntime as ort
        from tokenizers import Tokenizer
        
        self._session = ort.InferenceSession(str(EMBEDDING_MODEL_PATH))
        self._tokenizer = Tokenizer.from_file(str(EMBEDDING_TOKENIZER_PATH))
        log.info(f"Embedder loaded successfully from {EMBEDDING_MODEL_PATH}")

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into a normalized embedding vector.
        Returns float32 array of length EMBEDDING_DIM.
        """
        self._tokenizer.enable_padding(length=256)
        self._tokenizer.enable_truncation(max_length=256)
        
        encoded = self._tokenizer.encode(text)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)
        
        outputs = self._session.run(None, {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids
        })
        
        token_embeddings = outputs[0][0]
        mask = attention_mask[0].reshape(-1, 1).astype(np.float32)
        summed = (token_embeddings * mask).sum(axis=0)
        mask_sum = mask.sum()
        
        mean_pooled = summed / np.maximum(mask_sum, 1e-9)
        norm = np.linalg.norm(mean_pooled)
        result = mean_pooled / np.maximum(norm, 1e-9)
        
        return result.astype(np.float32)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode multiple texts at once. Used for bulk indexing."""
        results = [self.encode(t) for t in texts]
        return np.stack(results)
