# Quart Injector

<p class="lead">
Dependency injecetion for quart apps.
</p>

## 🛠 Installing

```
poetry add quart-injector
```

## 🎓 Usage

```py
import typing
import quart
import injector
import quart_injector

Greeting = typing.NewType("Greeting", str)


def configure(binder: injector.Binder) -> None:
    binder.bind(Greeting, to="Hello")


app = quart.Quart(__name__)


@app.route("/<name>")
@app.route("/", defaults={"name": "World"})
async def greeting_view(greeting: injector.Inject[Greeting], name: str) -> str:
    return f"{greeting} {name}!"


quart_injector.wire(app, configure)
```

## 📚 Help

See the [Documentation][docs] or ask questions on the [Discussion][discussions] board.

## ⚖️ Licence

This project is licensed under the [MIT licence][mit_licence].

All documentation and images are licenced under the 
[Creative Commons Attribution-ShareAlike 4.0 International License][cc_by_sa].

## 📝 Meta

This project uses [Semantic Versioning][semvar].

[docs]: https://quart-injector.artisan.io
[discussions]: https://github.com/artisanofcode/python-quart-injector/discussions
[mit_licence]: http://dan.mit-license.org/
[cc_by_sa]: https://creativecommons.org/licenses/by-sa/4.0/
[semvar]: http://semver.org/