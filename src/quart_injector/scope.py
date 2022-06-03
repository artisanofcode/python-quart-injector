"""
Request :class:`~injector.Scope`.
"""

import typing

import injector
import quart
import werkzeug.local

T = typing.TypeVar("T")


class RequestScope(injector.Scope):
    """
    Request scope

    A :class:`~injector.Scope` that returns a per-request instance for a key.
    """

    def configure(self) -> None:
        self._stack = werkzeug.local.LocalStack()

    def push(self) -> None:
        """
        Push new item onto stack.
        """
        self._stack.push({})

    def pop(self) -> None:
        """
        Remove topmost item from stack.
        """
        self._stack.pop()

    def get(self, key: type[T], provider: injector.Provider[T]) -> injector.Provider[T]:
        try:
            return self._stack.top[key]
        except KeyError:
            provider = injector.InstanceProvider(provider.get(self.injector))

            self._stack.top[key] = provider

            return provider


request = injector.ScopeDecorator(RequestScope)


def bind_scope(
    scope_cls: type[injector.Scope],
    app: quart.Quart,
    container: injector.Injector,
) -> None:
    """
    Bind scope.

    Bind the request scope class to applications before/teardown functions for requests
    and websockets.

    :param scope_cls: scope class to bind
    :param app: quart application
    :param container: dependency injection container
    """

    async def before_func() -> None:
        container.get(scope_cls).push()

    async def teardown_func(_: BaseException | None) -> None:
        container.get(scope_cls).pop()

    app.before_request_funcs[None].insert(0, before_func)
    app.before_websocket_funcs[None].insert(0, before_func)

    app.teardown_request_funcs[None].insert(0, teardown_func)
    app.teardown_websocket_funcs[None].insert(0, teardown_func)
