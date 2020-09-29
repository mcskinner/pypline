import inspect


def params(func):
    """Shorthand to get the parameter spec for a function."""
    return list(inspect.signature(func).parameters.values())


def param_map(func):
    return {p.name: p for p in params(func)}


def required_params(func):
    return [
        nm for nm, p in param_map(func).items()
        if p.default is p.empty
    ]


def optional_params(func):
    return [
        nm for nm, p in param_map(func).items()
        if p.default is not p.empty
    ]
