#!/usr/bin/env python

import functools

import fnspect


class Placeholder(object):
    """Placeholder for a thing that will arrive eventually.

    This is kind of like a Promise but without the chance of failure.
    """

    def __init__(self, name):
        self._name = name
        self._has = False
        self._val = None

    def name(self):
        return self._name

    def get(self):
        if not self._has:
            raise ValueError('no value set for `{}`'.format(self._name))
        return self._val

    def set(self, val):
        self._has = True
        self._val = val

    def unset(self):
        self._has = False


def with_placeholders(func):
    """Wrap a function to accept placeholders for some arguments."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args = [arg.get() if isinstance(arg, Placeholder) else arg for arg in args]
        return func(*args, **kwargs)
    return wrapper


def defer(*peels):
    if len(peels) != len(set(peels)):
        raise TypeError('duplicate args in {}'.format(peels))

    def decorator(func):
        pos_args = {
            p.name: i for i, p in enumerate(fnspect.params(func))
            if p.default is p.empty
        }
        vindex = []
        for peel in peels:
            if peel not in pos_args:
                raise TypeError('`{}` is not a positional param'.format(peel))
            vindex.append(pos_args[peel])

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            my_args = list(args)

            fakes = [Placeholder(peel) for peel in peels]
            for i, fake in zip(vindex, fakes):
                my_args = my_args[:i] + [fake] + my_args[i:]
            thunk = functools.partial(with_placeholders(func), *my_args, **kwargs)

            for param in fnspect.params(thunk):
                if param.default is param.empty:
                    raise TypeError('missing required positional param `{}`'.format(param.name))

            def most_inner_fn(*bound_args, **bound_kwargs):
                if len(bound_args) < len(fakes):
                    raise TypeError('missing deferred param `{}`'.format(
                        fakes[len(bound_args)].name()))

                for fake, peel in zip(fakes, bound_args):
                    fake.set(peel)

                try:
                    leftover_args = bound_args[len(fakes):]
                    return thunk(*leftover_args, **bound_kwargs)
                finally:
                    for fake in fakes:
                        fake.unset()

            return most_inner_fn
        return wrapper
    return decorator


def to_op(func, **kwargs):
    params = fnspect.params(func)

    # By convention first param is the input.
    op_in = params.pop(0)
    lfunc = functools.partial(func, **kwargs)
    return lfunc, op_in.name


@defer('a', 'b')
def some_func(a, b, c=9):
    print(100*a + 10*b + c)


def main():
    some_func(1)(2, 3)
    func, name = to_op(some_func, b=10)
    print(name, fnspect.required_params(func), fnspect.optional_params(func))


if __name__ == '__main__':
    main()
