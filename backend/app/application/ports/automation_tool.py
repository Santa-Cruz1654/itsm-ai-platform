from __future__ import annotations

from abc import ABC, abstractmethod


class AutomationTool(ABC):
    """
    Application port for a controlled automation tool.

    The self-healing workflow can execute only a registered,
    allowlisted AutomationTool.

    The tool itself does not decide whether execution is allowed.
    Policy and consent are evaluated before the tool is invoked.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        *,
        user_id: str,
    ) -> str:
        """
        Execute the controlled action for a user.

        Implementations must not accept arbitrary commands, scripts,
        URLs, or model-generated executable instructions.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        *,
        user_id: str,
    ) -> list[str]:
        """
        Validate that the requested action actually succeeded.

        Returns a list of concrete validation checks.
        """
        raise NotImplementedError