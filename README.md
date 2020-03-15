# Zen of MIP Modelling

At a really high level, some statements like those in [Zen of Python](https://www.python.org/dev/peps/pep-0020/) *might* be useful.
However I think the [CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines/blob/master/CppCoreGuidelines.md) are a better template.
They follow a general flow of:
1. General philosophical ideas (in general, prefer this style to this)
2. Specific recommendations (In this situtation, do this. Don't do this because **specific example of horrible consequences**)
3. They develop (or give a general specification of) toolkits that check your code against the guidelines or utilities that package up best practise.

**The aim should be to be strongly opinionated.**

# What could be useful

* Example projects
* Best practice guidelines (if this do that)
* Scaffolding/cookiecutters
* Utility functions that do things the right way

# Software engineering principles

Basic idea is that some of these are useful and some should be ignored.

## Object-oriented

Class heirarchys and whatnot are not very mathematical...
Classes are most useful for storing data, but they get overused for methods - either they have too few and should be replaced with a function, or they have too many and should be replaced with lots of smaller functions which take only the arguments they need.

## Globals

Globals are bad.
There is *always* (?) a way to do without them.
Everything should have scope.

## Functional Programming

Yes! Make pure functions as much as possible.
Most people err too much on the side of "performance" and lose hours of time debugging.

## Unit Testing

* Some styles aren't that useful.
* Property-based testing is incredibly useful.
* Be prepared to throw away your tests.

## Classes and Functions

### Bad uses of classes

* See [this talk](https://www.youtube.com/watch?v=o9pEzgHorH0)

This encourages classes being in an uninitialised state:

```python
class Model:
    def __init__(self):
        self._data = None

    def read(self, file_name):
        self._data = ...

model = Model()
model.read("/path/to/file")
```

Prefer a function that returns a fully initialised object:

```python
class Model:
    def __init__(self, data):
        self._data = data

def read_model(file_path):
    data = ...
    return Model(data)

model = read_model("/path/to/file")
```

### Good uses of classes

A static container for data is an excellent use of a class.
The [dataclasses](https://docs.python.org/3/library/dataclasses.html) package in the standard library (and backported as a pip installable package for older versions) is designed for exactly this use case.

**Reason:** Immutable objects and functions acting on them are easy to debug.

```python
from dataclasses import dataclass

@dataclass
class Task:
    earliest_start: float
    latest_start: float
    resources
```

Furthermore, a big list of classes (especially with the `__slots__` attribute set) has less performance overhead than a big list of dictionaries due to recent shared-key optimisations in the CPython interpreter (see benchmarks).

Where immutability leads to performance overhead, a class with a well defined invariant should be used.
All public functions should error if they leave the object in a state where the invariant is violated.
Use `icontracts` to enforce this.
