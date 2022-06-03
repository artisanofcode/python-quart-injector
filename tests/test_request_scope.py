"""
Tests for :class:`~quart_injector.RequestScope`.
"""
import injector

import quart_injector


class EmptyClass:  # pylint: disable=too-few-public-methods
    """
    Empty class.
    """


class DependsOnEmptyClass:
    """
    Depends on EmptyClass.

    A class depending on EmptyClass.

    :param child: instance of the class
    """

    # pylint: disable=too-few-public-methods

    @injector.inject
    def __init__(self, child: EmptyClass) -> None:
        self.child = child


@quart_injector.request
class ScopedEmptyClass:  # pylint: disable=too-few-public-methods
    """
    Scoped empty class.

    Like EmptyClass but decorated with the request scope
    """


class DependsOnScopedEmptyClass:
    """
    Depends on ScopedEmptyClass.

    A class depending on ScopedEmptyClass.

    :param child: instance of the class
    """

    # pylint: disable=too-few-public-methods

    @injector.inject
    def __init__(self, child: ScopedEmptyClass) -> None:
        self.child = child


def test_it_should_provide_same_values_within_request_scope() -> None:
    """
    it should provide same values within request scope
    """

    def configure(binder: injector.Binder) -> None:
        binder.bind(DependsOnEmptyClass)
        binder.bind(EmptyClass, scope=quart_injector.RequestScope)

    container = injector.Injector(configure)

    container.get(quart_injector.RequestScope).push()
    instance1 = container.get(DependsOnEmptyClass)
    instance2 = container.get(DependsOnEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    assert instance1.child is instance2.child


def test_it_should_provide_different_values_per_request_scope() -> None:
    """
    it should provide different values per request scope
    """

    def configure(binder: injector.Binder) -> None:
        binder.bind(DependsOnEmptyClass)
        binder.bind(EmptyClass, scope=quart_injector.RequestScope)

    container = injector.Injector(configure)

    container.get(quart_injector.RequestScope).push()
    instance1 = container.get(DependsOnEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    container.get(quart_injector.RequestScope).push()
    instance2 = container.get(DependsOnEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    assert instance1.child is not instance2.child


def test_it_should_provide_same_values_within_request_scope_using_decorator() -> None:
    """
    it should provide same values within request scope using decorator
    """

    def configure(binder: injector.Binder) -> None:
        binder.bind(DependsOnScopedEmptyClass)
        binder.bind(ScopedEmptyClass)

    container = injector.Injector(configure)

    container.get(quart_injector.RequestScope).push()
    instance1 = container.get(DependsOnScopedEmptyClass)
    instance2 = container.get(DependsOnScopedEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    assert instance1.child is instance2.child


def test_it_should_provide_different_values_per_request_scope_using_decorator() -> None:
    """
    it should provide different values per request scope using decorator
    """

    def configure(binder: injector.Binder) -> None:
        binder.bind(DependsOnScopedEmptyClass)
        binder.bind(ScopedEmptyClass)

    container = injector.Injector(configure)

    container.get(quart_injector.RequestScope).push()
    instance1 = container.get(DependsOnScopedEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    container.get(quart_injector.RequestScope).push()
    instance2 = container.get(DependsOnScopedEmptyClass)
    container.get(quart_injector.RequestScope).pop()

    assert instance1.child is not instance2.child
