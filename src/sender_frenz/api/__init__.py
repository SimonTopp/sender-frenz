"""HTTP API layer for sender-frenz.

Entry point for uvicorn::

    uvicorn sender_frenz.api:app
"""

from sender_frenz.api.app import app

__all__ = ["app"]
