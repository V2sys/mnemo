"""
mnemo/ai/query_engine.py
Owner: Vedansh

The brain. Takes a plain-English user query, retrieves relevant memories,
synthesizes a response via Phi-3, and returns a QueryResponse.

Also handles intent classification: is this a question or an action request?
"""

import logging

from mnemo.ai.phi3 import Phi3Engine, inference_pool
from mnemo.memory.embedder import Embedder
from mnemo.memory.store import MemoryStore
from mnemo.schema import (
    QueryRequest,
    QueryResponse,
    QuerySource,
    ActionPayload,
    SIMILARITY_THRESHOLD,
    TOP_K_DEFAULT,
    NOT_FOUND_FALLBACK,
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
        # TODO(week 3):
        # 1. Classify intent (ANSWER vs ACTION) via Phi-3
        # 2. If ACTION: parse target, return QueryResponse with action payload
        # 3. If ANSWER:
        #    a. embed query → query_vector
        #    b. results = store.search(query_vector, top_k, type_filter)
        #    c. if best similarity > SIMILARITY_THRESHOLD: confidence = "high"
        #    d. else if NOT_FOUND_FALLBACK: return closest with confidence "low"
        #    e. else: return response_type "not_found"
        #    f. build context from sources, call Phi-3 synthesis prompt
        #    g. return QueryResponse
        raise NotImplementedError("Vedansh — week 3 deliverable")

    def _classify_intent(self, query: str) -> str:
        """Returns 'ANSWER' or 'ACTION'."""
        # TODO(week 3)
        raise NotImplementedError("Vedansh — week 3 deliverable")

    def _parse_action(self, query: str) -> ActionPayload:
        """Parse an action command into an ActionPayload."""
        # TODO(week 3): use Phi-3 with a strict JSON output prompt
        raise NotImplementedError("Vedansh — week 3 deliverable")

    def _synthesize(self, query: str, sources: list[QuerySource]) -> str:
        """Generate the natural-language answer."""
        # TODO(week 3)
        raise NotImplementedError("Vedansh — week 3 deliverable")
