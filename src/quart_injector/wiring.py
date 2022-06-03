"""
Wire up :class:`~quart.Quart` application to :class:`~injector.Injector` instance.
"""


import collections.abc
import inspect
import typing
import functools

import quart
import quart.views
import injector

import quart_injector.scope
import quart_injector.module


def _wrap_view_class(
    view_func: collections.abc.Callable,
    app: quart.Quart,
    container: injector.Injector,
) -> collections.abc.Callable:
    cls: type[quart.views.View] = typing.cast(typing.Any, view_func).view_class

    while getattr(view_func, "__wrapped__", None):  # pylint: disable=while-used
        view_func = view_func.__wrapped__

    closure = inspect.getclosurevars(view_func)

    if closure.nonlocals.get("class_args"):
        raise RuntimeError(
            "cannot pass positional args to View.as_view() when using quart-injector"
        )

    class_kwargs = closure.nonlocals["class_kwargs"]

    async def view(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        self = container.create_object(cls, additional_kwargs=class_kwargs)

        dispatch_request = app.ensure_async(self.dispatch_request)

        return await dispatch_request(*args, **kwargs)

    if cls.decorators:
        view.__name__ = cls.__name__
        view.__module__ = cls.__module__
        for decorator in cls.decorators:
            view = decorator(view)

    setattr(view, "view_class", cls)
    view.__name__ = cls.__name__
    view.__doc__ = cls.__doc__
    view.__module__ = cls.__module__
    setattr(view, "methods", cls.methods)
    setattr(view, "provide_automatic_options", cls.provide_automatic_options)

    return view


def wrap(
    view_func: collections.abc.Callable,
    app: quart.Quart,
    container: injector.Injector,
) -> collections.abc.Callable:
    """
    Wrap

    Wrap the given view function for dependency injection.

    :param view_func: view function or class based view
    :param app: quart application
    :param container: dependency injection container

    :return: wrapped view function
    """

    if hasattr(view_func, "view_class"):
        return _wrap_view_class(view_func, app, container)

    async_func = app.ensure_async(view_func)

    @functools.wraps(view_func)
    async def view(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return await container.call_with_injection(async_func, None, args, kwargs)

    return view


def _wire_collection(
    value: typing.Any,
    app: quart.Quart,
    container: injector.Injector,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (list, dict)):
                _wire_collection(item, app, container)
            else:
                value[key] = wrap(item, app, container)

    if isinstance(value, list):
        value[:] = [wrap(item, app, container) for item in value]


def wire(
    app: quart.Quart,
    modules: injector._InstallableModuleType
    | collections.abc.Iterable[injector._InstallableModuleType]
    | None = None,
    auto_bind: bool = True,
    parent: injector.Injector | None = None,
) -> None:
    """
    Wire.

    Wire up a dependency injection container to the given application.

    :param app: quart application
    :param modules: configuration module or iterable of configuration modules
    :param auto_bind: whether to automatically bind missing types
    :param parent: dependency injection container
    """
    if not modules:
        modules = []

    if not isinstance(modules, collections.abc.Iterable):
        modules = [modules]

    modules.insert(0, quart_injector.module.QuartModule(app))

    container = injector.Injector(modules, auto_bind, parent)

    app.extensions["injector"] = container

    _wire_collection(app.after_request_funcs, app, container)
    _wire_collection(app.after_websocket_funcs, app, container)
    _wire_collection(app.before_request_funcs, app, container)
    _wire_collection(app.before_websocket_funcs, app, container)
    _wire_collection(app.error_handler_spec, app, container)
    _wire_collection(app.teardown_request_funcs, app, container)
    _wire_collection(app.teardown_websocket_funcs, app, container)
    _wire_collection(app.template_context_processors, app, container)
    _wire_collection(app.view_functions, app, container)

    quart_injector.scope.bind_scope(quart_injector.scope.RequestScope, app, container)
