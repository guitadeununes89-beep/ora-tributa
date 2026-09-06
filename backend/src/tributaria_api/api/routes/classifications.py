"""Compatibility import for the persisted classification router.

The former in-memory endpoint was removed in foundation stage three.
"""

from tributaria_api.api.routes.persisted_classifications import router

__all__ = ["router"]
