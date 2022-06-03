# Quick start 

```{rst-class} lead
On your mark, get set, GO!
```

## Greeter 

An example web application to greet people.


### Custom types

When dependencies are common types like strings, creating more specific types is 
helpful. The {obj}`typing.NewType` method is useful here. We define a `Greeting` type
but it could have been something like `DatabaseURL`.

```py
import typing


Greeting = typing.NewType("Greeting", str)
```

### Defining dependencies

You define dependencies  using an {class}`injector.Module`. Or a simple  function with 
an {class}`injector.Binder` instance as a parameter.

```py
import injector


def configure(binder: injector.Binder) -> None:
    binder.bind(Greeting, to="Hello")
```

### The web bits

Create a quart web application as usual. Adding the {obj}`injector.Inject` annotations 
to mark external dependencies in views. The framework will handle passing these values.

```py
import injector
import quart


app = quart.Quart(__name__)


@app.route("/<name>")
@app.route("/", defaults={"name": "World"})
async def greeting_view(greeting: injector.Inject[Greeting], name: str) -> str:
    return f"{greeting} {name}!"
```

### Wireing it up

Finally we wire everything together with the {meth}`~quart_injector.wire` method.

```py
import quart_injector

quart_injector.wire(app, modules=[configure])
```