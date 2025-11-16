"""Custom exceptions for RAG API.

This module defines typed exceptions that map to specific HTTP status codes
and provide structured error responses to API clients.
"""


class RagException(Exception):
    """Base exception for RAG API errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling across the API.

    Attributes:
        status_code: HTTP status code to return
        detail: Human-readable error message
    """

    def __init__(self, detail: str, status_code: int = 500):
        """Initialize RAG exception.

        Args:
            detail: Error message describing what went wrong
            status_code: HTTP status code (default: 500)
        """
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)


class EmbeddingError(RagException):
    """Exception raised when embedding model operations fail.

    This includes model loading failures, embedding generation errors,
    or any issues with the embedding model backend.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, detail: str):
        """Initialize embedding error.

        Args:
            detail: Error message describing the embedding failure
        """
        super().__init__(detail=detail, status_code=500)


class IndexNotFoundError(RagException):
    """Exception raised when a requested knowledge bank does not exist.

    This occurs when trying to query or retrieve stats for a bank
    that has not been created via upsert.

    HTTP Status: 404 Not Found
    """

    def __init__(self, detail: str):
        """Initialize index not found error.

        Args:
            detail: Error message identifying the missing bank
        """
        super().__init__(detail=detail, status_code=404)


class InvalidRequestError(RagException):
    """Exception raised when request validation fails.

    This includes malformed request bodies, invalid parameters,
    or any client-side errors in the request data.

    HTTP Status: 400 Bad Request
    """

    def __init__(self, detail: str):
        """Initialize invalid request error.

        Args:
            detail: Error message describing what is invalid
        """
        super().__init__(detail=detail, status_code=400)


class ModelNotLoadedError(RagException):
    """Exception raised when embedding model is not available.

    This occurs when the API receives requests but the embedding
    model has not been loaded yet or failed to load during startup.

    HTTP Status: 503 Service Unavailable
    """

    def __init__(self, detail: str):
        """Initialize model not loaded error.

        Args:
            detail: Error message about model availability
        """
        super().__init__(detail=detail, status_code=503)


class IndexWriteError(RagException):
    """Exception raised when writing to vector index fails.

    This includes file system errors, permission issues, or
    failures during index serialization.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, detail: str):
        """Initialize index write error.

        Args:
            detail: Error message describing the write failure
        """
        super().__init__(detail=detail, status_code=500)


class ChunkingError(RagException):
    """Exception raised when text chunking fails.

    This includes tokenization errors, invalid chunk parameters,
    or other issues during document chunking.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, detail: str):
        """Initialize chunking error.

        Args:
            detail: Error message describing the chunking failure
        """
        super().__init__(detail=detail, status_code=500)
