"""
Custom Exceptions for AIKU
"""

from fastapi import HTTPException, status


class AIKUException(Exception):
    """Base exception for AIKU"""
    def __init__(self, message: str, code: str = "AIKU_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(AIKUException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(AIKUException):
    """Authorization failed"""
    def __init__(self, message: str = "You don't have permission to perform this action"):
        super().__init__(message, "AUTHZ_ERROR")


class ToolExecutionError(AIKUException):
    """Tool execution failed"""
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool '{tool_name}' failed: {message}", "TOOL_ERROR")
        self.tool_name = tool_name


class OrchestrationError(AIKUException):
    """Orchestration failed"""
    def __init__(self, message: str = "Orchestration failed"):
        super().__init__(message, "ORCHESTRATION_ERROR")


class LLMError(AIKUException):
    """LLM API error"""
    def __init__(self, message: str = "LLM request failed"):
        super().__init__(message, "LLM_ERROR")


class ExternalAgentError(AIKUException):
    """External agent API error"""
    def __init__(self, agent_name: str, message: str):
        super().__init__(f"External agent '{agent_name}' failed: {message}", "EXTERNAL_AGENT_ERROR")
        self.agent_name = agent_name


# HTTP Exceptions
def unauthorized_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(detail: str = "Not enough permissions") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def not_found_exception(resource: str = "Resource") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found",
    )


def bad_request_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )
