#!/usr/bin/env python

import functools
import inspect


def fn_params(func):
    return inspect.signature(func).parameters.values()


def defer(*peels):
    def decorator(func):
        pos_args = {
            p.name: i for i, p in enumerate(fn_params(func))
            if p.default is p.empty
        }
        vindex = []
        for peel in peels:
            if peel not in pos_args:
                raise TypeError('`{}` is not a positional param'.format(peel))
            vindex.append(pos_args[peel])

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def most_inner_fn(*peeled_args):
                if len(vindex) != len(peeled_args):
                    raise TypeError('expected {} args, got {}'.format(
                        len(vindex), len(peeled_args)))

                my_args = list(args)
                for i, peel in zip(vindex, peeled_args):
                    my_args = my_args[:i] + [peel] + my_args[i:]
                return func(*my_args, **kwargs)
            return most_inner_fn
        return wrapper
    return decorator


@defer('a', 'b')
def some_func(a, b, c=10):
    print(a + b * c)


def main():
    some_func(100)(2, 3)


if __name__ == '__main__':
    main()
