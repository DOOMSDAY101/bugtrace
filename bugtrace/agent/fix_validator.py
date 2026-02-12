# bugtrace/analyze/fix_validator.py

from typing import Dict, Any
from bugtrace.llm.base import Message, BaseLLM


VALIDATION_PROMPT = """
You are reviewing a proposed code fix.

Your task:
1. Verify the fix uses only existing classes, methods, and attributes
2. Check for logical or runtime errors
3. Confirm the fix would work as written
4. If incorrect, provide a corrected fix
5. If correct, explain why

Rules:
- Do NOT invent new classes, attributes, or services
- Respect object boundaries shown in the code
- Prefer correctness over confidence

Be strict. Assume this will be applied to production code.

Here is the original code context:
{context}

Here is the proposed fix:
{response}
"""


class FixValidator:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def validate(
        self,
        context_text: str,
        original_response: str,
    ) -> str:
        """
        Validate and possibly correct an LLM-generated fix.
        """
        prompt = VALIDATION_PROMPT.format(
            context=context_text,
            response=original_response,
        )

        messages = [
            Message(role="system", content="You are a senior software engineer performing a code review."),
            Message(role="user", content=prompt),
        ]

        return self.llm.chat(messages)
