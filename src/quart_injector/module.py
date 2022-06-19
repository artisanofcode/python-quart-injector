"""
Quart :class:`~injector.Module`.
"""
import logging

import injector
import quart
import quart.sessions


class QuartModule(injector.Module):
    """
    Quart module.

    :param app: quart application
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, app: quart.Quart) -> None:
        self.app = app

    def configure(self, binder: injector.Binder) -> None:
        binder.bind(quart.Quart, to=self.app, scope=injector.singleton)
        binder.bind(quart.Config, to=self.app.config, scope=injector.singleton)
        binder.bind(quart.Request, to=lambda: quart.request)
        binder.bind(quart.sessions.SessionMixin, to=lambda: quart.session)
        binder.bind(quart.Websocket, to=lambda: quart.websocket)
        binder.bind(logging.Logger, to=self.app.logger)
