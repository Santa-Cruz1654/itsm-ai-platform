from __future__ import annotations

from app.application.ports.automation_tool import (
    AutomationTool,
)


class MockPasswordResetTool(AutomationTool):
    """
    Safe mock implementation of password reset.

    This does NOT modify a real account.

    It simulates the external identity-management action so the
    self-healing workflow can be demonstrated end-to-end.

    Production replacement:

        RealPasswordResetTool

    could call an approved identity-management API while keeping
    the same AutomationTool contract.
    """

    TOOL_NAME = "password_reset"

    def __init__(
        self,
        *,
        should_succeed: bool = True,
    ) -> None:
        self._should_succeed = should_succeed
        self._executed_users: list[str] = []

    @property
    def name(self) -> str:
        return self.TOOL_NAME

    def execute(
        self,
        *,
        user_id: str,
    ) -> str:
        user_id = user_id.strip()

        if not user_id:
            raise ValueError(
                "User ID cannot be empty."
            )

        if not self._should_succeed:
            raise RuntimeError(
                "Mock password reset provider unavailable."
            )

        self._executed_users.append(user_id)

        return "password_reset_successful"

    def validate(
        self,
        *,
        user_id: str,
    ) -> list[str]:
        user_id = user_id.strip()

        if not user_id:
            raise ValueError(
                "User ID cannot be empty."
            )

        if user_id not in self._executed_users:
            raise RuntimeError(
                "Password reset validation failed."
            )

        return [
            "password_reset_request_accepted",
            "password_reset_action_completed",
            "password_reset_state_validated",
        ]

    def was_executed_for(
        self,
        user_id: str,
    ) -> bool:
        return user_id in self._executed_users