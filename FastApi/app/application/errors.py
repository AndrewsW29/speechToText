"""Application-level errors, translated to HTTP problems at the inbound adapter."""


class ApplicationError(Exception):
    """Base class for expected, user-facing failures."""


class InvalidAudioError(ApplicationError):
    """The audio payload is empty or unusable."""


class TranscriptionError(ApplicationError):
    """The speech-to-text engine failed or returned nothing."""


class NoRelevantSourcesError(ApplicationError):
    """Retrieval found nothing to ground an answer on; we refuse to invent one."""


class ClassificationError(ApplicationError):
    """The intent classifier is unavailable or returned an unusable result."""
