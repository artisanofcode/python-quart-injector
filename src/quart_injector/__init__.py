"""
:class:`~injector.Injector` support for :class:`~quart.Quart` applications.
"""

from quart_injector.module import QuartModule
from quart_injector.scope import RequestScope, request
from quart_injector.wiring import wire, wrap

__all__ = (
    "QuartModule",
    "request",
    "RequestScope",
    "wire",
    "wrap",
)
