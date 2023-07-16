"""
Tests for :class:`~quart_injector.wrap`.
"""
import collections.abc
import functools
import re
import typing

import injector
import pytest
import quart
import quart.views

import quart_injector


class EmptyClass:  # pylint: disable=too-few-public-methods
    """
    Empty class.
    """


@pytest.mark.asyncio
async def test_it_should_wrap_functions_with_injector() -> None:
    """
    it should wrap functions with injector
    """
    app = quart.Quart(__name__)

    args: list[typing.Any] = [None, None]

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    @injector.inject
    def view(arg: str, empty: EmptyClass) -> str:
        args[0] = arg
        args[1] = empty

        return "bar"

    wrapped = quart_injector.wrap(view, app, container)

    assert await wrapped(arg="foo") == "bar"
    assert args[0] == "foo"
    assert isinstance(args[1], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_wrap_functions_with_injector_using_annotation() -> None:
    """
    it should wrap functions with injector using annotation
    """
    app = quart.Quart(__name__)

    args: list[typing.Any] = [None, None]

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    def view(arg: str, empty: injector.Inject[EmptyClass]) -> str:
        args[0] = arg
        args[1] = empty

        return "bar"

    wrapped = quart_injector.wrap(view, app, container)

    assert await wrapped(arg="foo") == "bar"
    assert args[0] == "foo"
    assert isinstance(args[1], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_wrap_async_functions_with_injector() -> None:
    """
    it should wrap async functions with injector
    """
    app = quart.Quart(__name__)

    args: list[typing.Any] = [None, None]

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    @injector.inject
    async def view(arg: str, empty: EmptyClass) -> str:
        args[0] = arg
        args[1] = empty

        return "bar"

    wrapped = quart_injector.wrap(view, app, container)

    assert await wrapped(arg="foo") == "bar"
    assert args[0] == "foo"
    assert isinstance(args[1], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_wrap_class_based_views_with_injector() -> None:
    """
    it should wrap class based views with injector
    """
    app = quart.Quart(__name__)

    _args: list[typing.Any] = [None, None, None]

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    @injector.inject
    class _View(quart.views.View):
        methods = ["GET"]

        def __init__(self, arg: str, empty: EmptyClass) -> None:
            self.arg = arg
            self.empty = empty

        async def dispatch_request(  # pylint: disable=unused-argument
            self,
            *args: typing.Any,
            **kwargs: typing.Any,
        ) -> str:
            _args[0] = self.arg
            _args[1] = self.empty
            _args[2] = kwargs["arg"]

            return "baz"

    view = _View.as_view("view", arg="foo")

    wrapped = quart_injector.wrap(view, app, container)

    assert await wrapped(arg="bar") == "baz"
    assert _args[0] == "foo"
    assert isinstance(_args[1], EmptyClass)
    assert _args[2] == "bar"


@pytest.mark.asyncio
async def test_it_should_error_when_wrapping_class_based_views_with_args() -> None:
    """
    it should error when wrapping class based views with positional arguments
    """
    app = quart.Quart(__name__)

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    @injector.inject
    class _View(quart.views.View):  # pragma: no cover
        methods = ["GET"]

        def __init__(self, arg: str, empty: EmptyClass) -> None:
            self.arg = arg
            self.empty = empty

        async def dispatch_request(  # pylint: disable=unused-argument
            self,
            *args: typing.Any,
            **kwargs: typing.Any,
        ) -> str:
            return "baz"

    view = _View.as_view("view", "foo")

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "cannot pass positional args to View.as_view() when using quart-injector"
        ),
    ):
        quart_injector.wrap(view, app, container)


@pytest.mark.asyncio
async def test_it_should_wrap_class_based_views_using_decorators() -> None:
    """
    it should wrap class based views using decorators
    """
    app = quart.Quart(__name__)

    _args: list[typing.Any] = [None, None, None]

    def configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    container = injector.Injector(configure)

    def decorator(
        func: collections.abc.Callable[..., str]
    ) -> collections.abc.Callable[..., str]:
        @functools.wraps(func)
        def wrapper() -> str:
            return func(arg="bar")

        return wrapper

    @injector.inject
    class _View(quart.views.View):
        methods = ["GET"]

        decorators = [decorator]

        def __init__(self, arg: str, empty: EmptyClass) -> None:
            self.arg = arg
            self.empty = empty

        async def dispatch_request(  # pylint: disable=unused-argument
            self,
            *args: typing.Any,
            **kwargs: typing.Any,
        ) -> str:
            _args[0] = self.arg
            _args[1] = self.empty
            _args[2] = kwargs["arg"]

            return "baz"

    view = _View.as_view("view", arg="foo")

    wrapped = quart_injector.wrap(view, app, container)

    assert await wrapped() == "baz"
    assert _args[0] == "foo"
    assert isinstance(_args[1], EmptyClass)
    assert _args[2] == "bar"
