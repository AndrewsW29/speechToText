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


class GenerationError(ApplicationError):
    """The answer generator (LLM) is unavailable or returned nothing usable."""


class TransientError(ApplicationError):
    """A failure worth retrying with backoff (network blip, scanner restarting, storage hiccup)."""


class UploadRejectedError(ApplicationError):
    """The upload is refused before any expensive work; the message is safe to show the user."""


class NotAPdfError(UploadRejectedError):
    def __init__(self, message: str = "This file isn't a valid PDF") -> None:
        super().__init__(message)


class TooLargeError(UploadRejectedError):
    pass


class TooManyPagesError(UploadRejectedError):
    pass


class QuotaExceededError(UploadRejectedError):
    pass


class MalwareFoundError(ApplicationError):
    """The scanner flagged the file; the document is quarantined and never parsed."""


class ScannerUnavailableError(TransientError):
    """The malware scanner could not be reached; ingestion fails closed and retries."""


class StorageError(TransientError):
    pass


class QueueUnavailableError(TransientError):
    pass


class ReaderNotConfiguredError(ApplicationError):
    """No reader/indexer is wired in this deployment, so the document cannot be processed yet."""


class PixelBudgetExceededError(UploadRejectedError):
    """Rendering this page would exceed the pixel cap (decompression-bomb protection)."""
