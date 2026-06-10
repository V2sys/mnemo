"""
mnemo/ai/phi3.py
Owner: Vedansh

Single point of LLM access. Loads Phi-3 Mini via llama-cpp-python.
Use the Vulkan/DirectML backend if available — see docs/setup.md.

CRITICAL: All inference goes through `inference_pool` (1 worker).
This prevents concurrent calls that would OOM on low-spec hardware
and keeps the model loaded between calls without thrashing.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from mnemo.config import PHI3_MODEL_PATH

log = logging.getLogger(__name__)


class Phi3Engine:
    def __init__(self) -> None:
        self._llm = None

    def load(self) -> None:
        """Load the model. Call once at startup."""
        if self._llm is not None:
            return  # Already loaded

        if not PHI3_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {PHI3_MODEL_PATH}. "
                "Please download the GGUF model and place it in the models directory."
            )

        log.info(f"Loading Phi-3 Mini from {PHI3_MODEL_PATH}")
        
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=str(PHI3_MODEL_PATH),
                n_ctx=4096,
                n_threads=4,
                n_gpu_layers=-1,   # offload all to GPU if Vulkan/DirectML
                verbose=False,
            )
            log.info("Phi-3 Mini loaded successfully.")
        except ImportError as e:
            raise ImportError(
                "llama-cpp-python is not installed. Please install it using the requirements.txt."
            ) from e

    def unload(self) -> None:
        """Release model from memory."""
        if self._llm is not None:
            del self._llm
            self._llm = None
            import gc
            gc.collect()
            log.info("Phi-3 unloaded from memory")

    @property
    def is_loaded(self) -> bool:
        return self._llm is not None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.3,
    ) -> str:
        """Run inference. Blocking. Use through inference_pool, not directly."""
        if self._llm is None:
            raise RuntimeError("Model is not loaded. Call load() before generate().")

        try:
            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|end|>", "User:", "Assistant:"],
                echo=False
            )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            log.error(f"Inference failed: {e}")
            raise


# ─────────────────────────────────────────────────────────────────
# Inference pool — used by both summarizer and query_engine
# Size MUST stay at 1. Concurrent LLM calls will OOM on weak GPUs.
# ─────────────────────────────────────────────────────────────────

inference_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="phi3")
"""
Usage:
    future = inference_pool.submit(phi3_engine.generate, prompt)
    result = future.result()   # blocks calling thread, UI stays responsive
"""
