from __future__ import annotations

from dataclasses import dataclass

from app.application.knowledge.context_assembly_service import RAGContext
from app.application.ports.llm_provider import LLMProvider


@dataclass(frozen=True)
class RAGAnswer:
    """
    Final answer produced from an assembled RAG context.

    The original RAG context is preserved so that callers can
    expose the knowledge sources used to generate the answer.
    """

    answer: str
    context: RAGContext


class RAGGenerationService:
    """
    Application service responsible for LLM generation over
    an already-assembled RAG context.

    Responsibilities:
        - validate the RAG context
        - construct the LLM prompt
        - invoke the injected LLM provider
        - validate the generated answer
        - preserve the original RAG context

    This service does NOT:
        - perform retrieval
        - access Qdrant
        - generate embeddings
        - know which LLM is being used
        - know whether the LLM runs locally or remotely
        - know whether inference uses CPU or GPU
    """

    def __init__(
        self,
        *,
        llm_provider: LLMProvider,
    ) -> None:
        self._llm_provider = llm_provider

    def generate(
        self,
        context: RAGContext,
    ) -> RAGAnswer:
        """
        Generate a grounded answer from the supplied RAG context.
        """

        if not context.query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        prompt = self._build_prompt(context)

        answer = self._llm_provider.generate(prompt)

        if not isinstance(answer, str):
            raise TypeError(
                "LLM provider must return a string"
            )

        answer = answer.strip()

        if not answer:
            raise ValueError(
                "LLM response cannot be empty"
            )

        return RAGAnswer(
            answer=answer,
            context=context,
        )

    @staticmethod
    def _build_prompt(
        context: RAGContext,
    ) -> str:
        """
        Build a deterministic grounded-generation prompt.

        The LLM receives:
            1. the user's question
            2. only the approved retrieved knowledge context

        Source metadata remains part of the context so the model
        can understand where the information came from.
        """

        return f"""
You are an enterprise IT service assistant.

Your task is to answer the employee's question using ONLY
the approved enterprise knowledge provided below.

Grounding rules:
1. Use the supplied knowledge context as the primary source of truth.
2. Do not invent procedures, policies, commands, or facts.
3. Do not rely on unsupported assumptions.
4. If the knowledge context does not contain enough information,
   clearly say that the available knowledge base does not provide
   enough information to answer the question.
5. Do not fabricate a solution merely to provide an answer.
6. Give concise, practical guidance suitable for an enterprise employee.
7. Preserve important warnings or limitations contained in the context.
8. Do not expose internal implementation details unless they are
   necessary for the employee to understand the solution.

USER QUESTION:
{context.query}

APPROVED KNOWLEDGE CONTEXT:
{context.context_text}
""".strip()