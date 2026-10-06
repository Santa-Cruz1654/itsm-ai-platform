from enum import StrEnum


class TicketType(StrEnum):
    INCIDENT = "incident"
    REQUEST = "request"


class TicketStatus(StrEnum):
    NEW = "new"
    ANALYZING = "analyzing"
    OPEN = "open"
    PENDING_USER = "pending_user"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class AutomationStatus(StrEnum):
    REQUESTED = "requested"
    POLICY_CHECK = "policy_check"
    AUTHORIZED = "authorized"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    DENIED = "denied"
    FAILED = "failed"
    ESCALATED = "escalated"


class ConsentSource(StrEnum):
    EXPLICIT_USER_REQUEST = "explicit_user_request"
    USER_CONFIRMATION = "user_confirmation"
    NOT_REQUIRED = "not_required"


class PolicyDecision(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"

class ConversationStatus(StrEnum):
    ACTIVE = "active"
    WAITING_FOR_USER = "waiting_for_user"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class MessageRole(StrEnum):
    EMPLOYEE = "employee"
    AI = "ai"
    SYSTEM = "system"


class ResolutionType(StrEnum):
    SELF_SERVICE = "self_service"
    AUTOMATION = "automation"
    INCIDENT_CREATED = "incident_created"
    REQUEST_CREATED = "request_created"
    UNRESOLVED = "unresolved"


class IntentType(StrEnum):
    """
    Closed set of AI workflow intents.

    These values represent what the employee is trying to accomplish,
    not the lifecycle/state of a Ticket.
    """

    KNOWLEDGE_QUESTION = "knowledge_question"
    INCIDENT = "incident"
    SERVICE_REQUEST = "service_request"
    AUTOMATABLE_ISSUE = "automatable_issue"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    """
    Application-level confidence classification.

    This is intentionally categorical rather than a calibrated
    probability. A future decision engine may derive this value from
    multiple signals such as structured-output validity, retrieval
    evidence, and business rules.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"