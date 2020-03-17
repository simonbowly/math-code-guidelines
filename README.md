# Zen of (Python?) Programming for Optimisation

*Work in progress!! I've written this readme page as a sort of aggressively aspirational list of best practice. Next task is to collect a lot of code examples and add/remove/edit these guidelines as we go.*

**The first programmers were mathematicians: so we should really be better at this than everyone else.**

## Why write this?

Some depressingly huge fraction of programmers are focused on website and app development.
This means the advice you'll find by searching for good software development and testing practices is pretty skewed towards this style of coding.
Much of it doesn't apply to the type of coding required to build optimisation algorithms, but there are useful nuggets out there we can compile into something useful.

## How to write this?

While the [Zen of Python](https://www.python.org/dev/peps/pep-0020/) sounds nice, I think the [CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines/blob/master/CppCoreGuidelines.md) are a better template (maybe not as epically long though).
They follow a general flow of:
1. General philosophical ideas (in general, prefer this style to this).
2. Specific recommendations (In this situtation, do this. Don't do that because **specific example of horrible consequences**).
3. They develop (or give a general specification of) toolkits that check your code against the guidelines (e.g. clang-tidy) or utilities that package up best practice to make it easier to use (e.g. the GSL).

I think guides like this should be strongly opinionated, with an "if you do this, you're probably doing it wrong".
The aim is to nudge new programmers towards best practice; it doesn't prevent a good programmer from going in a different direction, but should make it clear that "if you do it this way, you'd better know what you're doing".

# Programming Concepts

Python let's you do pretty much anything, so it's important to know what's appropriate when.

## Fail-fast, early, and totally

If you're relying heavily on the debugger, you're probably spending a lot of time waiting for one part of the code to execute so you can check what the state of all your variables are.

Chances are you've written code that doesn't have a well-defined state.
This point is **critical** and a lot of the concepts outlined below will help to write code that has well-defined state.

* Polluted namespaces (lots of variables in scope) make for complex states that are hard to reason about.
They also make it easy to confuse variable names and introduce accidental bugs.
* Well-defined and comprehensive assertions ensure that between each major set of instructions, your program is in the state you expect it to be in.
They also make it easier to understand what your code is doing.

Breaking your code down into well-defined functions acting on well-defined objects makes this much easier to achieve.
It also makes it much easier to include optional state checks that are descriptive for someone reading your code and can be disabled (but left in the code for future testing) once you start to use the code in anger.

Your code should fail quickly in testing if it finds itself in an unexpected state; you shouldn't have to inspect the runtime state to figure that out.
Your code should also fail quickly if someone tries to use it in an unexpected way.

## Object-oriented concepts

**Class heirarchies and inheritance are not useful.**

Best to get this one out of the way early: inheritance, polymorphism, class heirarchies, interfaces, etc are pretty much never useful for what we need to do.
Interfaces are only needed in statically typed languages where you need to know at compile time what methods are available for an object.
In a duck-typed language like Python, there's not a lot of reasons to use this.
Plus method resolution order seems to confuse the heck out of people.

The "composition over inheritance" rule applies here - assembling a big function or object out of smaller pieces is much cleaner than relying on the order of execution of methods in a class heirarchy.
Particularly when you forget to call `super()`.

## Classes/objects

**Objects/classes are very useful** (when used correctly).

The above does not mean classes and objects are not useful.
Objects are extremely useful if used correctly.

Here are the correct ways:

* Immutable objects. Immutable objects represent input and output data in a structured and descriptive way.
Because their data cannot change, there's no possibility of side effects.
Use frozen structures (`frozenset`, `tuple`) and [dataclasses](https://docs.python.org/3/library/dataclasses.html) to define them.

* Objects with well-defined invariants.
Classes help you to define a public API for methods that users of the object should call (users being functions or other classes).
Note that in Python there's no enforcement of public/private so you have to rely on naming conventions and documentation.
Before and after any public method is called on the object, invariant checks should be made.
These can be computationally expensive; a good library will allow them to be disabled with a runtime flag.

Here's a really common wrong way to write a class, which encourages a public method to be called and enforces no invariant.

```python
class Model:
    def __init__(self):
        self._data = None

    def read(self, file_name):
        self._data = ...

model = Model()
# BAD!! 'model' is currently in an invalid/unusable state.
model.read("/path/to/file")
```

This is the right way, where the user of the class can't make a mistake.

```python
class Model:
    def __init__(self, data):
        self._data = data

def read_model(file_path):
    data = ...
    return Model(data)

# In the client code, I either have an initialised model or I have nothing.
model = read_model("/path/to/file")
```

## Globals

**Global variables are bad.**

They introduce the potential for side effects, and there is **always** a way to do without them.
Everything should have a clear scope; almost everything should have a *local* scope.
Note that module level constants are not the same as global variables.

## Functions

**Write pure functions as much as possible.**

This means no side effects: the function has no state and its outputs are dependent only on its inputs.
For the same set of arguments it should return the same result every time.
Pure functions are very testable, functions that have or rely on side effects are hard to test.

The counter-argument is that pure functions result in a lot of copying of data.
However, ease of debugging and speed of development of pure functions more than compensates for performance overhead more often than you might think.
Most people err too much on the side of "performance" and lose hours of time debugging the results of side effects and mutability.

**Functions aren't just for reuse.**

They are intended to break down your code into digestible bits so you can reason effectively about the behaviour of the whole codebase and maintain a well-defined state as the code runs.

## Testing

**Test your code by running tests** (not by running it end to end).

* Use property-based testing, contracts and assertions.
When writing a function, assert conditions on your inputs and your outputs.
(You can do this with asserts but it's better to use a contracts library).
Then throw a lot of test cases at it using a property based testing library and code until your asserts pass.
* Write tests at a high level in your code.
You want your tests to run minimal but complete working examples on well defined APIs that hit as many code paths as possible so there are no surprises later.
* Be prepared to throw away your tests.
Sometimes you'll find a small test is helpful as you develop a function but it outlives its usefulness pretty quickly.
Throw it away if so ... don't confer intrinsic value on it just because it's a test.
Property based testing makes it easy to write tests without much code, so you don't get too invested.

# Tools to Use

* [pytest-cov](https://github.com/pytest-dev/pytest-cov) - `pytest --cov module --cov-report=html` - see whether the else in your if is actually being hit by your tests.
* [hypothesis](https://hypothesis.readthedocs.io/en/latest/) - generates data for property based testing.
* [icontract](https://github.com/Parquery/icontract) - for contract definition. This one is broken on python3.8 and is a little over-engineered IMO ... I'm working on a replacement or a fix :-)
* [black](https://black.readthedocs.io/en/stable/) - just let it take over. Drop pep8 and pylint. It will annoy you at first with some of its choices, but eventually you'll just give in.
* [mypy](https://github.com/python/mypy) - type checking is sometimes useful, but even without types it should catch a lot of undefined variable type errors that pep8 and pylint do, without doubling up on formatters and annoying you about line lengths. But ... this is really the job of tests.

# Benchmarks

The standard line is "don't make performance claims without benchmarks!".
More practically, know your tradeoffs between readability, mutability, reasonability, memory use, and speed.
Will put some useful test cases together here, starting with:

* [Tiny Object Benchmarks](benchmarks/Tiny-Object-Benchmarks.ipynb)
