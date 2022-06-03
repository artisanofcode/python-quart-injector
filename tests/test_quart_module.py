"""
Tests for :class:`~quart_injector.QuartModule`.
"""
import logging

import injector
import quart
import quart.sessions

import quart_injector


def test_it_should_return_passed_application() -> None:
    """
    it should return passed application
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    assert app == container.get(quart.Quart)


def test_it_should_return_passed_applications_configuration() -> None:
    """
    it should return passed applications configuration
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    assert app.config == container.get(quart.Config)


def test_it_should_return_request() -> None:
    """
    it should return request
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    assert quart.request == container.get(quart.Request)


def test_it_should_return_websocket() -> None:
    """
    it should return websocket
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    assert quart.websocket == container.get(quart.Websocket)


def test_it_should_return_session() -> None:
    """
    it should return session
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    # following is ignored as the type checker gets upset about abstract classes
    assert quart.session == container.get(quart.sessions.SessionMixin)  # type: ignore


def test_it_should_return_logger() -> None:
    """
    it should return logger
    """
    app = quart.Quart(__name__)

    container = injector.Injector(quart_injector.QuartModule(app))

    assert app.logger == container.get(logging.Logger)
