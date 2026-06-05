"""
mnemo/ai/query_engine.py
Owner: Vedansh

The brain. Takes a plain-English user query, retrieves relevant memories,
synthesizes a response via Phi-3, and returns a QueryResponse.

Also handles intent classification: is this a question or an action request?
"""

import logging
from typing import Literal

from mnemo.ai.phi3 import Phi3Engine, inference_pool
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import (
    SIMILARITY_THRESHOLD,
    TOP_K_DEFAULT,
    ActionPayload,
    QueryRequest,
    QueryResponse,
    QuerySource,
)

log = logging.getLogger(__name__)


INTENT_PROMPT = """<|user|>
Classify this user request as either ANSWER (a question to look up) or ACTION (a command to execute).
Respond with only one word.

Request: {query}
<|end|>
<|assistant|>"""


SYNTHESIS_PROMPT = """<|user|>
The user asked: {query}

Here is what their personal memory holds:
{context}

Answer the user's question using only the memory above. Be concise.
If the memory doesn't contain an answer, say so honestly.
<|end|>
<|assistant|>"""


class QueryEngine:
    def __init__(
        self,
        phi3: Phi3Engine,
        embedder: Embedder,
        store: MemoryStore,
    ) -> None:
        self.phi3 = phi3
        self.embedder = embedder
        self.store = store

    def handle(self, request: QueryRequest) -> QueryResponse:
        """Main entry point — UI calls this."""
        query = request["query"]
        
        # 1. Classify intent (ANSWER vs ACTION)
        intent = self._classify_intent(query)
        
        # 2. Handle ACTION
        if intent == "ACTION":
            # For Checkpoint 2, we just return a placeholder action.
            # Parsing complex actions is Week 3!
            action_payload: ActionPayload = {"type": "system_command", "target": query}
            return {
                "response_type": "action",
                "text": "Executing command...",
                "sources": [],
                "action": action_payload,
                "confidence": "high"
            }
            
        # 3. Handle ANSWER (Semantic Search)
        # a. Embed query
        query_vector = self.embedder.encode(query)
        
        # b. Search store
        top_k = request.get("top_k", TOP_K_DEFAULT)
        type_filter = request.get("type_filter")
        sources = self.store.search(query_vector, top_k=top_k, type_filter=type_filter)
        
        if not sources:
             return {
                "response_type": "not_found",
                "text": "I couldn't find anything in your memory about that.",
                "sources": [],
                "action": None,
                "confidence": "low"
            }
             
        # c. Check confidence
        best_sim = sources[0]["similarity"]
        # Note: Depending on the backend, similarity might be distance (closer to 0 is better) 
        # or cosine similarity (closer to 1 is better). Assuming cosine similarity here based on schema.
        # FIX: The backend actually computes vector distance, so a lower value is better!
        confidence: Literal["high", "low"] = "high" if best_sim <= SIMILARITY_THRESHOLD else "low"
        
        # d. Synthesize answer using Phi-3
        answer = self._synthesize(query, sources)
        
        return {
            "response_type": "answer",
            "text": answer,
            "sources": sources,
            "action": None,
            "confidence": confidence
        }

    def _classify_intent(self, query: str) -> str:
        """Returns 'ANSWER' or 'ACTION'."""
        prompt = INTENT_PROMPT.format(query=query)
        # Submit to the thread pool to prevent blocking/OOM
        future = inference_pool.submit(self.phi3.generate, prompt=prompt, max_tokens=10, temperature=0.1)
        response = future.result().strip().upper()
        
        if "ACTION" in response:
            return "ACTION"
        return "ANSWER"

    def _parse_action(self, query: str) -> ActionPayload:
        """Parse an action command into an ActionPayload."""
        # TODO(week 3): use Phi-3 with a strict JSON output prompt
        raise NotImplementedError("Vedansh — week 3 deliverable")

    def _synthesize(self, query: str, sources: list[QuerySource]) -> str:
        """Generate the natural-language answer."""
        # Bundle the retrieved summaries into a single context string
        context_blocks = []
        for i, source in enumerate(sources):
            mem_type = source["type"].upper()
            src_name = source.get("source", "Unknown")
            summary = source["summary"]
            context_blocks.append(f"[{i+1}] ({mem_type} MEMORY from '{src_name}'): {summary}")
            
        context_string = "\n\n".join(context_blocks)
        
        prompt = SYNTHESIS_PROMPT.format(query=query, context=context_string)
        
        # Submit to the thread pool
        future = inference_pool.submit(self.phi3.generate, prompt=prompt, max_tokens=300, temperature=0.3)
        answer = future.result().strip()
        
        return answer
