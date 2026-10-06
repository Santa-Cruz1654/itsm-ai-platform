from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    """
    Application-level abstraction for text generation.

    The application layer does not know:
        - which LLM is being used
        - where the model is hosted
        - whether inference runs on CPU or GPU
        - whether Transformers or another runtime is used

    Infrastructure implementations satisfy this contract.
    """

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the supplied prompt.

        Implementations must return only the generated answer,
        not the original prompt.
        """
        ...