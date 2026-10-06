

from __future__ import annotations



import json

from dataclasses import dataclass

from typing import Any



from pydantic import ValidationError



from app.application.ports.llm_provider import LLMProvider

from app.domain.enums import ConfidenceLevel, IntentType

from app.domain.intent import AIIntentAnalysis





class IntentAnalysisError(RuntimeError):

    """

    Raised when the LLM response cannot be converted into a valid

    AIIntentAnalysis.



    This is intentionally different from UNKNOWN.



    UNKNOWN means:

        The model successfully produced a valid analysis and the

        request was determined to be unsupported or unsafe to classify

        into a supported workflow.



    IntentAnalysisError means:

        The AI analysis itself could not be trusted because the model

        returned malformed or invalid structured output.

    """





@dataclass(frozen=True)

class IntentAnalyzerConfig:

    """

    Configuration for the intent-analysis application service.

    """



    max_retries: int = 1



    def __post_init__(self) -> None:

        if self.max_retries < 0:

            raise ValueError(

                "max_retries cannot be negative"

            )





class IntentAnalyzer:

    """

    Application service responsible for converting employee language

    into a validated AIIntentAnalysis.



    Responsibilities:



        - validate the employee request

        - construct the intent-analysis prompt

        - invoke the injected LLM provider

        - extract a JSON object from the response

        - validate the result using AIIntentAnalysis

        - apply deterministic classification safety rules

        - perform a bounded retry when structured output is invalid



    This service does NOT:



        - create tickets

        - execute automation

        - perform authorization

        - perform knowledge retrieval

        - generate employee-facing answers

        - access Qdrant

        - access MongoDB

        - access ServiceNow



    Important safety principle:



        LLM output is treated as a classification proposal.



        It is NOT treated as authoritative workflow authorization.



        After schema validation, deterministic safety rules are applied

        before the result is returned to the workflow layer.

    """



    # ------------------------------------------------------------------

    # Supported enterprise knowledge taxonomy

    # ------------------------------------------------------------------



    # These are the knowledge domains currently supported by the

    # enterprise knowledge base / ITSM demo.

    #

    # This is intentionally an allow-list rather than a deny-list.

    #

    # Example:

    #

    #   Outlook -> email/outlook -> supported

    #   VPN     -> network/vpn    -> supported

    #   SAP DB  -> database/...   -> unsupported -> UNKNOWN

    #

    SUPPORTED_KNOWLEDGE_CATEGORIES: frozenset[str] = frozenset(

        {

            "email",

            "network",

            "identity",

            "authentication",

            "mfa",

            "laptop",

            "software",

            "access",

        }

    )



    # Some supported domains have stable aliases used by the model.

    #

    # We normalize them before checking the allow-list so that a valid

    # supported request is not rejected merely because the model uses

    # an equivalent category name.

    KNOWLEDGE_CATEGORY_ALIASES: dict[str, str] = {

        "auth": "authentication",

        "account": "identity",

        "accounts": "identity",

        "credentials": "identity",

        "mail": "email",

        "outlook": "email",

        "wifi": "network",

        "wi-fi": "network",

        "wireless": "network",

        "computer": "laptop",

        "device": "laptop",

        "application": "access",

        "app": "access",

    }



    def __init__(

        self,

        *,

        llm_provider: LLMProvider,

        config: IntentAnalyzerConfig | None = None,

    ) -> None:

        self._llm_provider = llm_provider

        self._config = config or IntentAnalyzerConfig()



    # ------------------------------------------------------------------

    # Public API

    # ------------------------------------------------------------------



    def analyze(

        self,

        employee_request: str,

    ) -> AIIntentAnalysis:

        """

        Analyze an employee request and return a validated,

        safety-gated AIIntentAnalysis.



        Raises:



            ValueError:

                If the employee request is empty.



            IntentAnalysisError:

                If the LLM cannot produce valid structured analysis

                after the configured number of retries.

        """



        request = self._validate_request(

            employee_request

        )



        prompt = self._build_prompt(

            request

        )



        last_error: Exception | None = None

        raw_response = ""



        for attempt in range(

            self._config.max_retries + 1

        ):

            try:

                raw_response = (

                    self._llm_provider.generate(

                        prompt

                    )

                )



                if not isinstance(

                    raw_response,

                    str,

                ):

                    raise TypeError(

                        "LLM provider must return a string"

                    )



                raw_response = (

                    raw_response.strip()

                )



                if not raw_response:

                    raise ValueError(

                        "LLM response cannot be empty"

                    )



                payload = (

                    self._extract_json_object(

                        raw_response

                    )

                )



                analysis = (

                    AIIntentAnalysis.model_validate(

                        payload

                    )

                )



                # ------------------------------------------------------

                # ------------------------------------------------------
                # Deterministic ITSM policy enrichment
                # ------------------------------------------------------
                analysis = (
                    self._apply_deterministic_incident_defaults(
                        analysis
                    )
                )

                # Deterministic safety boundary

                # ------------------------------------------------------

                #

                # Pydantic validation only proves that the model

                # returned a structurally valid object.

                #

                # It does NOT prove that the classification is

                # semantically safe.

                #

                # Apply the deterministic enterprise-scope guard here.

                #

                return self._apply_safety_guardrails(

                    analysis,

                    employee_request=request,

                )



            except (

                json.JSONDecodeError,

                TypeError,

                ValueError,

                ValidationError,

            ) as exc:

                last_error = exc



                if (

                    attempt

                    >= self._config.max_retries

                ):

                    break



                prompt = (

                    self._build_repair_prompt(

                        employee_request=request,

                        invalid_response=raw_response,

                        validation_error=str(exc),

                    )

                )



        raise IntentAnalysisError(

            "LLM failed to produce valid structured intent "

            f"analysis after {self._config.max_retries + 1} "

            "attempt(s)"

        ) from last_error



    # ------------------------------------------------------------------

    # Deterministic safety boundary

    # ------------------------------------------------------------------



    # ------------------------------------------------------------------
    # Deterministic ITSM policy enrichment
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_deterministic_incident_defaults(
        analysis: AIIntentAnalysis,
    ) -> AIIntentAnalysis:
        """
        Apply deterministic ITSM metadata for the supported VPN incident.

        The LLM identifies the employee's problem. Operational ITSM
        metadata is controlled by deterministic policy so that the
        mandatory VPN incident workflow does not depend on the model
        consistently producing operational routing fields.
        """

        if (
    analysis.intent == IntentType.INCIDENT
    and (analysis.category or "").strip().lower() == "network"
    and (analysis.subcategory or "").strip().lower() == "vpn"
):
            return AIIntentAnalysis.model_validate(
                {
                    **analysis.model_dump(),
                    "priority": "P2",
                    "impact": "individual",
                    "urgency": "high",
                    "assignment_group": "network_support",
                }
            )

        return analysis


    def _apply_safety_guardrails(

        self,

        analysis: AIIntentAnalysis,

        *,

        employee_request: str,

    ) -> AIIntentAnalysis:

        """

        Apply deterministic safety rules after LLM classification.



        The LLM is responsible for semantic classification, but it is

        not allowed to authorize an unsupported knowledge workflow.



        The most important rule is:



            knowledge_question

                +

            unsupported knowledge category

                =>

            UNKNOWN



        This prevents an LLM from turning an arbitrary technical

        question into an apparently supported enterprise knowledge

        request.



        The rule is deliberately narrow:



        - Existing incident classification is preserved.

        - Existing service-request classification is preserved.

        - Existing automatable classification is preserved.

        - Supported knowledge categories are preserved.

        - Unsupported knowledge categories are converted to UNKNOWN.



        The converted UNKNOWN result uses MEDIUM confidence because

        the system has deterministic evidence that the request is

        outside the approved knowledge taxonomy, but we do not claim

        probabilistic certainty from the LLM.

        """



        if (

            analysis.intent

            != IntentType.KNOWLEDGE_QUESTION

        ):

            return analysis



        normalized_category = (

            self._normalize_knowledge_category(

                analysis.category

            )

        )



        if (

            normalized_category

            in self.SUPPORTED_KNOWLEDGE_CATEGORIES

        ):

            # Preserve the original analysis when the knowledge domain

            # is explicitly within the approved enterprise taxonomy.

            #

            # We do not rewrite the category here. The downstream

            # knowledge filters should continue to receive the model's

            # actual category value.

            return analysis



        return self._build_unknown_analysis(

            employee_request=employee_request,

            original_analysis=analysis,

        )



    @classmethod

    def _normalize_knowledge_category(

        cls,

        category: str | None,

    ) -> str | None:

        """

        Normalize a model-produced knowledge category.



        Returns None for missing/empty categories.

        """



        if category is None:

            return None



        normalized = (

            category

            .strip()

            .lower()

        )



        if not normalized:

            return None



        return cls.KNOWLEDGE_CATEGORY_ALIASES.get(

            normalized,

            normalized,

        )



    @staticmethod

    def _build_unknown_analysis(

        *,

        employee_request: str,

        original_analysis: AIIntentAnalysis,

    ) -> AIIntentAnalysis:

        """

        Convert an unsupported knowledge classification into the

        canonical UNKNOWN representation.



        We intentionally discard unsupported category/subcategory and

        software information so that downstream workflows cannot

        accidentally treat the unsupported domain as an approved

        enterprise capability.

        """



        return AIIntentAnalysis(

            intent=IntentType.UNKNOWN,

            category=None,

            subcategory=None,

            priority=None,

            impact=None,

            urgency=None,

            assignment_group=None,

            summary=(

                "Unsupported or unapproved enterprise "

                "ITSM knowledge request."

            ),

            confidence=ConfidenceLevel.MEDIUM,

            automation_candidate=False,

            software_name=None,

        )



    # ------------------------------------------------------------------

    # Prompt construction

    # ------------------------------------------------------------------



    @staticmethod

    def _build_prompt(

        employee_request: str,

    ) -> str:

        """

        Build a deterministic classification prompt.



        The classifier must prefer UNKNOWN whenever the request is

        outside supported enterprise ITSM workflows or cannot be

        classified reliably.



        The prompt remains a first-line defense.



        The deterministic safety gate in _apply_safety_guardrails()

        remains the final classification boundary.

        """



        return f"""

You are the intent-classification component of an enterprise ITSM

system.



Your ONLY task is to classify the employee request and return one

structured JSON object.



Do not answer the employee.

Do not provide troubleshooting instructions.

Do not execute actions.

Do not invent workflow types.

Do not invent enterprise capabilities.

Do not assume that an unsupported technical topic is supported

by the enterprise ITSM system.

Do not include explanations outside the JSON object.



SUPPORTED INTENTS



1. knowledge_question



The employee wants information, instructions, or guidance about a

SUPPORTED enterprise IT topic.



Currently supported knowledge domains include:



- email / Outlook

- corporate network / VPN / Wi-Fi

- identity / password / authentication

- MFA / account lockout

- corporate laptop / device troubleshooting

- approved enterprise software

- approved enterprise application/access topics



Examples:



- "How do I troubleshoot Outlook synchronization?"

- "How do I reset my corporate password?"

- "How do I troubleshoot the company Wi-Fi?"



2. incident



Something is broken, unavailable, failing, or behaving incorrectly

within a supported enterprise IT environment.



Examples:



- "My VPN isn't working."

- "My laptop is extremely slow."

- "Outlook stopped syncing."



3. service_request



The employee wants a new IT service, software, access, device,

account capability, or other provisioned enterprise IT item.



Examples:



- "Install Visual Studio Code on my laptop."

- "I need access to the finance application."

- "I need Microsoft Teams installed."



4. automatable_issue



The issue is a known operational problem that may be handled by

a controlled automation workflow.



Example:



- "My password has expired."



5. unknown



Use UNKNOWN when:



- the request is outside supported enterprise ITSM scope

- the request concerns an unsupported enterprise system

- the request concerns an unsupported technical domain

- the request cannot be mapped reliably to a supported ITSM workflow

- there is insufficient information to classify it safely

- answering would require inventing enterprise knowledge or

  capabilities

- the request is about a technical system for which no approved

  enterprise knowledge domain is available



UNKNOWN EXAMPLES



"How do I configure the company's SAP production database replication?"

-> unknown



"How do I restart the SAP production database replication service?"

-> unknown



"Explain quantum gravity and provide the mathematical derivation."

-> unknown



"How do I repair my refrigerator?"

-> unknown



"How do I configure a nuclear reactor?"

-> unknown



"Tell me how the company's undocumented production database works."

-> unknown



IMPORTANT CLASSIFICATION RULE



Do NOT classify a request as knowledge_question merely because

the request is phrased as a question.



A question about an unsupported enterprise system or unsupported

technical domain must be classified as UNKNOWN.



For example:



"How do I configure the company's SAP production database replication?"



must be:



unknown



not:



knowledge_question



Do not assume that the enterprise has approved documentation for

a system merely because the system name is recognizable.



SUPPORTED KNOWLEDGE DOMAIN RULE



A knowledge_question must belong to one of the currently supported

enterprise knowledge domains:



- email

- network

- identity

- authentication

- MFA

- laptop

- software

- access



If the request is a knowledge question about a different domain,

classify it as UNKNOWN.



CLASSIFICATION EXAMPLES



"How do I troubleshoot Outlook synchronization?"

-> knowledge_question



"My VPN isn't working."

-> incident



"Install Visual Studio Code on my laptop."

-> service_request



"My password has expired."

-> automatable_issue



"How do I configure the company's SAP production database replication?"

-> unknown



"How do I restart the SAP production database replication service?"

-> unknown



"Explain quantum gravity."

-> unknown



"How do I repair my refrigerator?"

-> unknown



OUTPUT RULES



Return ONLY valid JSON.



The JSON object MUST contain exactly these fields:



{{

  "intent": "knowledge_question | incident | service_request | automatable_issue | unknown",

  "category": "string or null",

  "subcategory": "string or null",

  "priority": "string or null",

  "impact": "string or null",

  "urgency": "string or null",

  "assignment_group": "string or null",

  "summary": "string",

  "confidence": "low | medium | high",

  "automation_candidate": true,

  "software_name": "string or null"

}}



FIELD RULES



- intent must be one of the five supported values.

- category should describe the IT domain only when identifiable.

- subcategory should describe the specific issue only when identifiable.

- priority, impact, urgency, and assignment_group should be null

  when they cannot be determined reliably.

- summary must be concise and describe the employee's request.

- confidence must be low, medium, or high.

- automation_candidate must be true only when the request appears

  suitable for a controlled automation workflow.

- software_name should only be populated when a specific software

  product is clearly mentioned.

- Never invent missing information.

- For UNKNOWN requests, category and subcategory should normally

  be null.

- For UNKNOWN requests, automation_candidate must be false.

- When uncertain between a supported intent and UNKNOWN, prefer

  UNKNOWN with low or medium confidence.



EMPLOYEE REQUEST



{employee_request}

""".strip()



    @staticmethod

    def _build_repair_prompt(

        *,

        employee_request: str,

        invalid_response: str,

        validation_error: str,

    ) -> str:

        """

        Build a bounded repair prompt.



        The repair attempt is intentionally stricter than the initial

        prompt. It does not ask the model to reconsider the task;

        it asks it to produce only a schema-valid JSON object while

        preserving the UNKNOWN safety rules.

        """



        return f"""

You are repairing a failed structured ITSM classification.



Return ONLY one valid JSON object.



Do not include:

- markdown

- code fences

- explanations

- comments

- multiple JSON objects

- additional fields

- reasoning



Allowed intent values:



- knowledge_question

- incident

- service_request

- automatable_issue

- unknown



Allowed confidence values:



- low

- medium

- high



Required JSON schema:



{{

  "intent": "knowledge_question | incident | service_request | automatable_issue | unknown",

  "category": "string or null",

  "subcategory": "string or null",

  "priority": "string or null",

  "impact": "string or null",

  "urgency": "string or null",

  "assignment_group": "string or null",

  "summary": "string",

  "confidence": "low | medium | high",

  "automation_candidate": true,

  "software_name": "string or null"

}}



SAFETY RULES



A knowledge_question is allowed only for the currently supported

enterprise knowledge domains:



- email

- network

- identity

- authentication

- MFA

- laptop

- software

- access



Unsupported enterprise systems or technical domains MUST be:



unknown



Examples:



"How do I configure the company's SAP production database replication?"

-> unknown



"How do I restart the SAP production database replication service?"

-> unknown



"Explain quantum gravity."

-> unknown



"How do I troubleshoot Outlook synchronization?"

-> knowledge_question



"How do I troubleshoot the company Wi-Fi?"

-> knowledge_question



Original employee request:



{employee_request}



Previous invalid model response:



{invalid_response}



Validation/parsing problem:



{validation_error}



Return the corrected JSON object now.

""".strip()



    # ------------------------------------------------------------------

    # Input validation

    # ------------------------------------------------------------------



    @staticmethod

    def _validate_request(

        employee_request: str,

    ) -> str:

        """

        Validate and normalize the employee request.

        """



        if not isinstance(

            employee_request,

            str,

        ):

            raise ValueError(

                "employee_request must be a string"

            )



        request = (

            employee_request.strip()

        )



        if not request:

            raise ValueError(

                "employee_request cannot be empty"

            )



        return request



    # ------------------------------------------------------------------

    # JSON extraction

    # ------------------------------------------------------------------



    @staticmethod

    def _extract_json_object(

        response: str,

    ) -> dict[str, Any]:

        """

        Extract exactly one JSON object from an LLM response.



        The model may occasionally wrap JSON in markdown or include

        short surrounding text. We tolerate that formatting without

        accepting arbitrary non-JSON content as valid data.



        A JSON object is decoded using JSONDecoder.raw_decode rather

        than fragile regular expressions.

        """



        text = response.strip()



        if not text:

            raise ValueError(

                "LLM response cannot be empty"

            )



        # First try the complete response. This is the expected path.

        try:

            payload = json.loads(text)



            if not isinstance(

                payload,

                dict,

            ):

                raise TypeError(

                    "LLM response must contain a JSON object"

                )



            return payload



        except json.JSONDecodeError:

            pass



        decoder = json.JSONDecoder()



        candidates: list[

            dict[str, Any]

        ] = []



        for index, character in enumerate(

            text

        ):

            if character != "{":

                continue



            try:

                payload, _ = (

                    decoder.raw_decode(

                        text[index:]

                    )

                )

            except json.JSONDecodeError:

                continue



            if isinstance(

                payload,

                dict,

            ):

                candidates.append(

                    payload

                )



        if not candidates:

            raise ValueError(

                "LLM response does not contain a valid JSON object"

            )



        if len(candidates) > 1:

            raise ValueError(

                "LLM response contains multiple JSON objects"

            )



        return candidates[0]
