"""
view class example
"""

import typing
import quart
import quart.views
import injector
import quart_injector


Greeting = typing.NewType("Greeting", str)


def configure(binder: injector.Binder) -> None:
    """
    Configure container

    :param binder: container binder
    """
    binder.bind(Greeting, to="Hello")


app = quart.Quart(__name__)


class GreetingView(quart.views.MethodView):
    """
    Greeting view

    ;param greeting: greeting phrase
    :param punctuation: punctuation character for after name
    """

    def __init__(self, greeting: injector.Inject[Greeting], punctuation: str) -> None:
        self.greeting = greeting
        self.punctuation = punctuation

    methods = {"GET"}

    async def get(self, name: str) -> str:
        """
        Get

        :param name: name to greet

        :returns: body
        """

        return f"{self.greeting} {name}{self.punctuation}"


greeting_view = GreetingView.as_view("greeting_view", punctuation="!")

app.add_url_rule("/", view_func=greeting_view, defaults={"name": "World"})
app.add_url_rule("/<name>", "greeting_view")

quart_injector.wire(app, configure)
