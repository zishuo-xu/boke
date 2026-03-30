class ChatDomainError(Exception):
    """Base exception for chat domain failures."""


class UnsupportedProviderError(ChatDomainError):
    """Raised when a provider has no registered adapter."""


class InvalidChatRequestError(ChatDomainError):
    """Raised when a chat request violates domain rules."""


class SessionNotFoundError(ChatDomainError):
    """Raised when a chat session does not exist."""


class AgentNotFoundError(ChatDomainError):
    """Raised when an agent does not exist."""
