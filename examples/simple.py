"""
simple example
"""

import typing

import injector
import quart

import quart_injector

Greeting = typing.NewType("Greeting", str)


def configure(binder: injector.Binder) -> None:
    """
    Configure container

    :param binder: container binder
    """
    binder.bind(Greeting, to="Hello")


app = quart.Quart(__name__)


@app.route("/<name>")
@app.route("/", defaults={"name": "World"})
async def greeting_view(greeting: injector.Inject[Greeting], name: str) -> str:
    """
    Greeting view

    :param greeting: greeting phrase
    :param name: name to greet

    :returns: body
    """
    return f"{greeting} {name}!"


quart_injector.wire(app, configure)
