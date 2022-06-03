"""
Tests for :class:`~quart_injector.wire`.
"""
import typing

import injector
import pytest
import quart

import quart_injector


class EmptyClass:  # pylint: disable=too-few-public-methods
    """
    Empty class.
    """


class CustomError(Exception):
    """
    Custom error.
    """


def configure(binder: injector.Binder) -> None:
    """
    Configure injector.

    Bind empty class to the request scope.
    """
    binder.bind(EmptyClass, scope=quart_injector.RequestScope)


async def view() -> str:
    """
    View.

    A simple view for testing.
    """
    return "content here"


async def template_view() -> str:
    """
    Template view.

    A view to for testing templates.
    """
    return await quart.render_template_string("{{ content }}", content="content here")


async def error_view() -> str:
    """
    Error view.

    A view to for testing error handling.
    """
    raise CustomError()


async def websocket() -> None:
    """
    Websocket.

    A simple websocket for testing.
    """
    message = await quart.websocket.receive()
    await quart.websocket.send(message)


def factory() -> quart.Quart:
    """
    Factory.

    Simple application factory for testing.
    """
    app = quart.Quart(__name__)
    app.add_url_rule("/", view_func=view)
    app.add_url_rule("/error", view_func=error_view)
    app.add_url_rule("/template", view_func=template_view)
    app.add_websocket("/ws", view_func=websocket)

    return app


def blueprint_factory() -> tuple[quart.Quart, quart.Blueprint]:
    """
    Blueprint factory.

    Simple application factory for testing.
    """
    app = quart.Quart(__name__)

    blueprint = quart.Blueprint("foo", __name__)

    blueprint.add_url_rule("/", view_func=view)
    blueprint.add_url_rule("/error", view_func=error_view)
    blueprint.add_url_rule("/template", view_func=template_view)
    blueprint.add_websocket("/ws", view_func=websocket)

    return app, blueprint


def test_it_should_attach_container_to_application() -> None:
    """
    it should attach container to application
    """
    app = quart.Quart(__name__)

    quart_injector.wire(app)

    assert isinstance(app.extensions["injector"], injector.Injector)


def test_it_should_register_single_function_with_container() -> None:
    """
    it should register single function with container
    """
    app = quart.Quart(__name__)

    def _configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    quart_injector.wire(app, _configure)

    assert isinstance(app.extensions["injector"].get(EmptyClass), EmptyClass)


def test_it_should_register_collection_of_functions_with_container() -> None:
    """
    it should register collection of functions with container
    """
    app = quart.Quart(__name__)

    def _configure(binder: injector.Binder) -> None:
        binder.bind(EmptyClass)

    quart_injector.wire(app, [_configure])


def test_it_should_register_default_module_with_container() -> None:
    """
    it should register default module with container
    """
    app = quart.Quart(__name__)

    quart_injector.wire(app)

    assert app.extensions["injector"].get(quart.Quart) is app
    assert app.extensions["injector"].get(quart.Config) is app.config


def test_it_should_register_default_module_first() -> None:
    """
    it should register default module with container
    """
    app = quart.Quart(__name__)

    config = quart.Config("/tmp", {})

    def _configure(binder: injector.Binder) -> None:
        binder.bind(quart.Config, to=config)

    quart_injector.wire(app, _configure)

    assert app.extensions["injector"].get(quart.Quart) is app
    assert app.extensions["injector"].get(quart.Config) is config


def test_it_should_pass_auto_bind_to_container() -> None:
    """
    it should pass auto bind to container
    """
    auto_bind_app = quart.Quart(__name__)
    quart_injector.wire(auto_bind_app, auto_bind=True)

    non_auto_bind_app = quart.Quart(__name__)
    quart_injector.wire(non_auto_bind_app, auto_bind=False)

    # pylint: disable=protected-access
    assert isinstance(auto_bind_app.extensions["injector"].get(EmptyClass), EmptyClass)

    with pytest.raises(
        injector.UnsatisfiedRequirement,
        match="unsatisfied requirement on EmptyClass",
    ):
        non_auto_bind_app.extensions["injector"].get(EmptyClass)


def test_it_should_register_parent_with_container() -> None:
    """
    it should register parent with container
    """
    app = quart.Quart(__name__)

    parent = injector.Injector()

    quart_injector.wire(app, parent=parent)

    assert app.extensions["injector"].parent is parent


@pytest.mark.asyncio
async def test_it_should_inject_into_app_after_request_function() -> None:
    """
    it should inject into app.after_request function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.after_request  # type: ignore
    @injector.inject
    async def _(response: quart.Response, empty: EmptyClass) -> quart.Response:
        args[0] = empty

        return response

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_after_websocket_function() -> None:
    """
    it should inject into app.after_websocket function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.after_websocket  # type: ignore
    @injector.inject
    async def _(
        response: quart.Response | None,
        empty: EmptyClass,
    ) -> quart.Response | None:
        args[0] = empty

        return response

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_before_request_function() -> None:
    """
    it should inject into app.before_request function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.before_request  # type: ignore
    @injector.inject
    async def _(empty: EmptyClass) -> None:
        args[0] = empty

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_before_websocket_function() -> None:
    """
    it should inject into app.before_websocket function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.before_websocket  # type: ignore
    @injector.inject
    async def _(
        empty: EmptyClass,
    ) -> None:
        args[0] = empty

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_errorhandler_function() -> None:
    """
    it should inject into app.error handler function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.errorhandler(CustomError)  # type: ignore
    @injector.inject
    async def _(_: CustomError, empty: EmptyClass) -> str:
        args[0] = empty

        return "foo"

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/error")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_teardown_request_function() -> None:
    """
    it should inject into app.teardown_request function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.teardown_request  # type: ignore
    @injector.inject
    async def _(_: BaseException | None, empty: EmptyClass) -> None:
        args[0] = empty

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_teardown_websocket_function() -> None:
    """
    it should inject into app.teardown_websocket function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.teardown_websocket  # type: ignore
    @injector.inject
    async def _(_: BaseException | None, empty: EmptyClass) -> None:
        args[0] = empty

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_context_processor_function() -> None:
    """
    it should inject into app.context_processor function.
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.context_processor  # type: ignore
    @injector.inject
    async def _(empty: EmptyClass) -> dict[str, typing.Any]:
        args[0] = empty

        return {}

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/template")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_app_views() -> None:
    """
    it should inject into app views
    """
    app = factory()

    args: list[typing.Any] = [None]

    @app.route("/test")
    @injector.inject
    async def _(empty: EmptyClass) -> str:
        args[0] = empty

        return "content here"

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/test")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_after_request_function() -> None:
    """
    it should inject into blueprint.after_request function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.after_request  # type: ignore
    @injector.inject
    async def _(response: quart.Response, empty: EmptyClass) -> quart.Response:
        args[0] = empty

        return response

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_after_websocket_function() -> None:
    """
    it should inject into blueprint.after_websocket function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.after_websocket  # type: ignore
    @injector.inject
    async def _(
        response: quart.Response | None,
        empty: EmptyClass,
    ) -> quart.Response | None:
        args[0] = empty

        return response

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_before_request_function() -> None:
    """
    it should inject into blueprint.before_request function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.before_request  # type: ignore
    @injector.inject
    async def _(empty: EmptyClass) -> None:
        args[0] = empty

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_before_websocket_function() -> None:
    """
    it should inject into blueprint.before_websocket function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.before_websocket  # type: ignore
    @injector.inject
    async def _(
        empty: EmptyClass,
    ) -> None:
        args[0] = empty

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_errorhandler_function() -> None:
    """
    it should inject into blueprint.error handler function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.errorhandler(CustomError)  # type: ignore
    @injector.inject
    async def _(_: CustomError, empty: EmptyClass) -> str:
        args[0] = empty

        return "foo"

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/error")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_teardown_request_function() -> None:
    """
    it should inject into blueprint.teardown_request function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.teardown_request  # type: ignore
    @injector.inject
    async def _(_: BaseException | None, empty: EmptyClass) -> None:
        args[0] = empty

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_teardown_websocket_function() -> None:
    """
    it should inject into blueprint.teardown_websocket function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.teardown_websocket  # type: ignore
    @injector.inject
    async def _(_: BaseException | None, empty: EmptyClass) -> None:
        args[0] = empty

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    async with test_client.websocket("/ws") as test_websocket:
        await test_websocket.send("foo")
        assert await test_websocket.receive() == "foo"

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_context_processor_function() -> None:
    """
    it should inject into blueprint.context_processor function.
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.context_processor  # type: ignore
    @injector.inject
    async def _(empty: EmptyClass) -> dict[str, typing.Any]:
        args[0] = empty

        return {}

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/template")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_into_blueprint_views() -> None:
    """
    it should inject into blueprint views
    """
    app, blueprint = blueprint_factory()

    args: list[typing.Any] = [None]

    @blueprint.route("/test")
    @injector.inject
    async def _(empty: EmptyClass) -> str:
        args[0] = empty

        return "content here"

    app.register_blueprint(blueprint)

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/test")

    assert isinstance(args[0], EmptyClass)


@pytest.mark.asyncio
async def test_it_should_inject_consistent_values_inside_request() -> None:
    """
    it should inject consistent values inside request
    """

    app = factory()

    args: list[typing.Any] = [None, None]

    @app.before_request  # type: ignore
    @injector.inject
    async def _(empty: EmptyClass) -> None:
        args[0] = empty

    @app.after_request  # type: ignore
    @injector.inject
    async def _(response: quart.Response, empty: EmptyClass) -> quart.Response:
        args[1] = empty

        return response

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/")

    assert isinstance(args[0], EmptyClass)
    assert args[0] is args[1]


@pytest.mark.asyncio
async def test_it_should_inject_differet_values_in_different_requests() -> None:
    """
    it should inject consistent values inside websocket
    """
    app = factory()

    args: list[typing.Any] = []

    @app.route("/test")
    @injector.inject
    async def _(empty: EmptyClass) -> str:
        args.append(empty)

        return "content here"

    quart_injector.wire(app, configure)

    test_client = app.test_client()

    await test_client.get("/test")
    await test_client.get("/test")

    assert isinstance(args[0], EmptyClass)
    assert isinstance(args[1], EmptyClass)
    assert args[0] is not args[1]
