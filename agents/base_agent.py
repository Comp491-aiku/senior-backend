"""
Base agent class with common functionality
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all AI agents
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task

        Args:
            context: Dictionary containing input data for the agent

        Returns:
            Dictionary containing the agent's output
        """
        pass

    def log_info(self, message: str):
        """Log an info message"""
        self.logger.info(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log an error message"""
        self.logger.error(f"[{self.name}] {message}")

    def log_debug(self, message: str):
        """Log a debug message"""
        self.logger.debug(f"[{self.name}] {message}")
