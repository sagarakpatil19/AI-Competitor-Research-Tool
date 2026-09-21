class AIProviderError(Exception):
    """Base error for provider-neutral AI failures."""


class ProviderUnavailableError(AIProviderError):
    """The provider could not accept or serve the request."""


class ProviderTimeoutError(AIProviderError):
    """The provider did not respond within the allowed time."""


class ProviderResponseError(AIProviderError):
    """The provider returned an unusable response."""


class ProviderInvalidOutputError(AIProviderError):
    """Provider output failed the structured contract or reference checks."""
