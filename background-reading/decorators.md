# Decorators

*Not to be confused with the decorator pattern in object oriented programming, however the spirit is kind of the same.*

Decorators add or alter behaviour of functions.

## Mechanics

Here's your basic decorator:

```python
# Define the decorator.
def decorate(func):
    def decorated(*args, **kwargs):
        print(f"Decorated function called with {args=} {kwargs=}")
        return func(*args, **kwargs)
    return decorated

# Decorate the function.
@decorate
def my_function(a, b):
    print(f"Original function called with {a=} {b=}")

my_function(1, 2)
```

We get this output when `my_function` is called:

```
Decorated function called with args=(1, 2) kwargs={}
Original function called with a=1 b=2
```

What's happenning?
The `@` notation here basically a shorthand to running `my_function = decorate(my_function)`.
This works because Python functions are just objects; things in the namespace that can be assigned to or modified.
The decoration (`@decorate`) calls `decorate(func)`, and replaces `my_function` with the result (which is the inner function `decorated`).

The inner function `decorated`, retains access to `func` (the original, undecorated `my_function`) and can pass through the arguments using `*args, **kwargs` unpacking.
This allows a generic decorator to add functionality to a variety of different functions.

## What is it good for?

[functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache) is a really useful example of a decorator.
The LRU (least-recently-used) cache can be used to store the result of a function call for a given set of arguments.
Essentially it does something like this:

```python
def lru_cache(func):
    """ Simple version. The real one also handles keyword arguments, and limits
    the cache size to only keep recent results. """
    cached_results = {}

    def func_with_cache(*args):
        if args not in cached_results:
            cached_results[args] = func(*args)
        return cached_results[args]

    return func_with_cache


@lru_cache
def pure_function(a, b):
    print("call")
    return a + b

pure_function(1, 2)    # The sum is computed.
pure_function(1, 2)    # The stored result is returned without recomputing.
```

The decorator replaces the original **pure function** (a pure function cannot have side effects - its result must depend only on its input arguments and it must always return the same result for the same arguments) with a function that has an attached dictionary of results.
On the first call with some arguments, the function is executed and its result is stored.
When the decorated function is called again, it attempts a lookup from the function arguments and returns the stored result instead of recomputing.

`lru_cache` is very useful as a shortcut for expensive computations.
A classic example is computing the Fibonnaci sequence recursively.
Without the decorator, this recursive approach would kick off a pretty large tree of function calls.

```python
from functools import lru_cache

@lru_cache
def fib(n):
    if n == 0 or n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)
```

functools also has the [cached_property](https://docs.python.org/3/library/functools.html#functools.cached_property) decorator which can be used on an instance method to lazily compute a property of an object (assuming the object is immutable).
See this example from the docs, where variance and standard deviation of the data will be computed only if they are requested, and only ever computed once.

```python
class DataSet:
    def __init__(self, sequence_of_numbers):
        self._data = sequence_of_numbers

    @cached_property
    def stdev(self):
        return statistics.stdev(self._data)

    @cached_property
    def variance(self):
        return statistics.variance(self._data)
```
