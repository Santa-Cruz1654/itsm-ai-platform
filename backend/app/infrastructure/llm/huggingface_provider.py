from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass(frozen=True)
class HuggingFaceLLMConfig:
    """
    Configuration for the local Hugging Face LLM.

    Qwen3-1.7B is intentionally used instead of the larger
    Qwen3-4B model because this application currently runs
    with CPU-only PyTorch and limited system memory.
    """

    model_name: str = "Qwen/Qwen3-1.7B"

    device: str = "cpu"

    max_new_tokens: int = 256

    temperature: float = 0.7

    top_p: float = 0.8

    repetition_penalty: float = 1.05

    enable_thinking: bool = False

    trust_remote_code: bool = True


class HuggingFaceLLMProvider:
    """
    Local Hugging Face LLM provider.

    Responsibilities:
        - load the tokenizer
        - load the Hugging Face model
        - apply the Qwen chat template
        - generate a response
        - return only the generated answer

    This provider does NOT:
        - perform retrieval
        - access Qdrant
        - assemble RAG context
        - create tickets
        - execute automation
        - access ServiceNow

    Those responsibilities belong to other application layers.
    """

    def __init__(
        self,
        config: HuggingFaceLLMConfig | None = None,
    ) -> None:
        self._config = config or HuggingFaceLLMConfig()

        self._tokenizer: Any | None = None
        self._model: Any | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """
        Generate a response from the local Hugging Face model.
        """

        prompt = prompt.strip()

        if not prompt:
            raise ValueError("prompt must not be empty")

        self._ensure_loaded()

        assert self._tokenizer is not None
        assert self._model is not None

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an enterprise IT service assistant. "
                    "Answer using only the information provided in "
                    "the user prompt. Do not invent enterprise "
                    "procedures, credentials, policies, or facts. "
                    "If the supplied knowledge is insufficient, "
                    "clearly say that the available knowledge base "
                    "does not contain enough information."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self._config.enable_thinking,
        )

        model_inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
        )

        model_inputs = {
            key: value.to(self._model.device)
            for key, value in model_inputs.items()
        }

        input_token_count = model_inputs["input_ids"].shape[-1]

        with torch.inference_mode():
            generated_ids = self._model.generate(
                **model_inputs,
                max_new_tokens=self._config.max_new_tokens,
                do_sample=True,
                temperature=self._config.temperature,
                top_p=self._config.top_p,
                repetition_penalty=self._config.repetition_penalty,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        generated_token_ids = generated_ids[
            0,
            input_token_count:,
        ]

        answer = self._tokenizer.decode(
            generated_token_ids,
            skip_special_tokens=True,
        ).strip()

        return self._clean_response(answer)

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """
        Lazily load the tokenizer and model.

        Lazy loading is intentional:
            importing the provider does not immediately allocate
            several gigabytes of memory.
        """

        if self._model is not None and self._tokenizer is not None:
            return

        self._tokenizer = self._load_tokenizer()
        self._model = self._load_model()

    def _load_tokenizer(self):
        return AutoTokenizer.from_pretrained(
            self._config.model_name,
            trust_remote_code=self._config.trust_remote_code,
        )

    def _load_model(self):
        """
        Load Qwen3-1.7B for CPU inference.

        We deliberately avoid device_map="auto" here because this
        machine currently has CPU-only PyTorch.

        low_cpu_mem_usage reduces peak memory during loading.
        """

        model = AutoModelForCausalLM.from_pretrained(
            self._config.model_name,
            dtype="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=self._config.trust_remote_code,
        )

        model.to(self._config.device)

        model.eval()

        return model

    # ------------------------------------------------------------------
    # Response cleanup
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_response(answer: str) -> str:
        """
        Remove accidental Qwen thinking blocks if they ever appear.

        Non-thinking mode is explicitly enabled, but this provides
        an additional safety boundary for the application.
        """

        if not answer:
            return ""

        if "<think>" in answer:
            _, answer = answer.split(
                "<think>",
                1,
            )

        if "</think>" in answer:
            answer = answer.split(
                "</think>",
                1,
            )[-1]

        return answer.strip()

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        return self._config.model_name

    @property
    def device(self) -> str:
        return self._config.device

    @property
    def is_loaded(self) -> bool:
        return (
            self._model is not None
            and self._tokenizer is not None
        )