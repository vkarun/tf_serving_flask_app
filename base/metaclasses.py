"""Defines useful metaclasses like singletons."""


class Singleton(type):
    """Defines a singleton metaclass.

    https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
