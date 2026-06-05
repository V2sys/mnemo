"""
mnemo/ai/summarizer.py
Owner: Vedansh

Generates Phi-3-powered summaries for capture pipeline.

Called by:
- Vinayak's screenshot.py (always, for screenshots)
- Vinayak's file_watcher.py (only when text > FILE_SUMMARY_CHAR_THRESHOLD)

Returns: a single string summary, capped at SUMMARY_MAX_CHARS.
"""

import logging

from mnemo.ai.phi3 import Phi3Engine
from mnemo.schema import SUMMARY_MAX_CHARS

log = logging.getLogger(__name__)


PROMPT_TEMPLATE = """<|user|>
You are summarizing content for a personal memory assistant.
Write a {max_chars}-character summary capturing what the user was doing or reading.
Focus on key topics, names, file names, and concepts.
Be specific and factual. No fluff.

Content:
{content}
<|end|>
<|assistant|>"""


class Summarizer:
    def __init__(self, phi3: Phi3Engine) -> None:
        self.phi3 = phi3

    def summarize(self, content: str) -> str:
        """Generate a summary. Run via inference_pool from the caller."""
        # Truncate content to avoid exceeding Phi-3's 4096 token context window
        # 4096 tokens is roughly ~16,000 chars. We truncate to 10,000 chars to be safe.
        safe_content = content[:10000]
        
        prompt = PROMPT_TEMPLATE.format(max_chars=SUMMARY_MAX_CHARS, content=safe_content)
        
        # We ask Phi-3 to generate the response
        result = self.phi3.generate(prompt, max_tokens=150)
        
        # Ensure we don't exceed the database column size limit
        return result.strip()[:SUMMARY_MAX_CHARS]
