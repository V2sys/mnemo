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

from mnemo.ai.phi3 import Phi3Engine, inference_pool
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
        # TODO(week 2):
        # prompt = PROMPT_TEMPLATE.format(max_chars=SUMMARY_MAX_CHARS, content=content)
        # return self.phi3.generate(prompt, max_tokens=200)[:SUMMARY_MAX_CHARS]
        raise NotImplementedError("Vedansh — week 2 deliverable")
