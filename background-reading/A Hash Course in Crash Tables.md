# Comparison and Hashing with `__eq__` and `__hash__`

First a quick hash course in crash tables (ahem) *crash course in hash tables*.
(Yes I'm falling well short of the Ballmer peak as a write this on a Monday night).

![Ballmer Peak](https://imgs.xkcd.com/comics/ballmer_peak.png)

## Step 1: Compute Hash

There are three steps to a lookup operation in Python (by a lookup here I mean checking whether something is in a `set`, or finding the value corresponding to a key in a `dict`).
The first is calling `hash()` on the object you're trying to use as a key.

The hash of an integer is itself:


```python
hash(1)
```




    1



The hash of other objects somehow munges its internal data to produce another integer


```python
print(hash((1, 2)))  # Hash of a tuple, not a hash of two things.
print(hash((1, 2)))
print(hash("abcde"))
print(hash("abcde"))
```

    -3550055125485641917
    -3550055125485641917
    3569808136850082918
    3569808136850082918


The hash of an object is based entirely on its data, and is invariant.
There are two exceptions:
* hashes of python strings are only the same *for a given run of the Python interpreter*
* hashes of instances of user-defined classes are, unless you implement the `__hash__` method, based on `id(...)` ... I'll get into that later

The string thing involves a random seed generated when the interpreter starts (this is called *salting* a hash), meaning you can't rely on the hash value remaining the same for different runs of a program.
I think this is the case because at some point people used Python's `hash` function to compute hashes for passwords.
This is a different kind of hash (a cryptographic hash).
Without salting your hash, you're vulnerable to pre-computed hash dictionary attacks, so this was included around Python 3.4 to address this inadvertent security flaw.
It's worth noting that you still should not use `hash` to hash passwords, you should use the stuff in `hashlib`.
BUT, in the immortal words of Andrew Folkard Perrykkad, I DIGRESS.

The long and the short of it is that the actual hash value does not matter.
What you *can* rely on is if two things compare equal, their hashes are the same.

`a == b -> hash(a) == hash(b)`

However, `hash(a) == hash(b)` does *not* imply that `a == b`.

There's another interesting digression here that I heard Raymond Hettinger (a Python core dev) mention in a PyCon talk I can no longer find.
He said the full test suite of CPython *still passes* if you remove the equality check used in dictionary key comparison (it's sufficient to compare hashes).
In other words, for the purposes of the Python tests (where dictionaries underly absolutely everything), `hash(a) == hash(b)` *does* imply `a == b`.
Not sure if this is a pro of the hash implementation or a con of the test suite... Python's hash implementation is pretty good at making unique hashes, is all I'm saying.

## Step 2: Stick in Hash Table

Your basic hash table (underlying a `dict` or `set` in Python), looks like this:

```
SLOT 0: [           ]
SLOT 1: [           ]
SLOT 2: [           ]
SLOT 3: [           ]
```

To add an object, I compute its hash, take its modulus w.r.t. the size of the hash table, and stick it in the appropriate spot.


```python
print(f"{hash((1, 51)) % 4 = }")    # New favourite Python3.8 f-string feature btw
print(f"{hash((13, 52)) % 4 = }")
```

    hash((1, 51)) % 4 = 1
    hash((13, 52)) % 4 = 3


With these objects inserted at `hash(obj) mod p`, the hash table looks like this:

```
SLOT 0: [           ]
SLOT 1: [  (1, 51)  ]
SLOT 2: [           ]
SLOT 3: [ (13, 52)  ]
```

I can now look up an object by computing its `hash mod p`.
If I land on an empty slot, the object must not be in the table, otherwise, I should be in the right place.

## Step 3: Check I Found What I'm Looking For

Having landed in the right slot of the hash table, I now just do an `==` comparison to verify that I've found what I'm looking for.

There's one more thing: hash collisions. If I try to stick the following object into my hash table:


```python
print(f"{hash((13, 51)) % 4 = }")
```

    hash((13, 51)) % 4 = 1


There's something already in slot 1, so I *probe* forward in the table until the next empty slot.
This is called *open addressing* or *closed hashing* (annoyingly, open hashing is the opposite of open addressing).
Once collisions start appearing, there's an extra step required to find my new `(13, 51)` value, since I need to hash it, go to slot 1, check equality (which fails), then probe forward while checking for equality until I find what I'm after or hit an empty slot.

```
SLOT 0: [           ]
SLOT 1: [  (1, 51)  ]
SLOT 2: [ (13, 51)  ]
SLOT 3: [ (13, 52)  ]
```

In practical cases, the hash table is maintained at a size large enough to keep plenty of gaps so probing distance is short.
For dictionaries, Python starts with a size 8 table, and proceeds to double in size whenever it becomes 2/3 full.

## One other thing

The hash of a mutable object can't be computed


```python
hash([1, 2, 3])
```


    ---------------------------------------------------------------------------

    TypeError                                 Traceback (most recent call last)

    <ipython-input-5-84d65be9aa35> in <module>
    ----> 1 hash([1, 2, 3])
    

    TypeError: unhashable type: 'list'


This is because you don't want to put a `list` as a key in a dict `set`, then be able to change the `list` while it's in there.
This would result in the `list` being in an unexpected position in the hashtable, breaking the entire data structure and invalidating all algorithms that could be used to find it.

# Now for the fun stuff

To use user-defined objects with hashable containers, you need to define `__eq__` and `__hash__` member functions.
If you don't, `==` among your classes becomes essentially equivalent to `is`, which might not be what you're after.

I'll use this little graph model to illustrate some of the weirdness involved with hashing user-defined classes.
The graph traversal algorithm just starts from one node, and traverses `key -> value` in the `graph` dictionary until it finds no neighbouring node.
In all these examples, starting at `3` should end at `6` unless something goes wrong.


```python
def go_to_end(graph, start):
    """ Traverse a graph. """
    while True:
        next_ = graph.get(start)
        if next_ is None:
            break
        start = next_
    return start

go_to_end(
    graph={3: 1, 1: 2, 2: 5, 5: 6},
    start=3,
)
```




    6



Excellent, it works with integers. Here's what happens when I define my own class:


```python
class Obj:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"{self.value = }"
```

This traverses succesfully ...


```python
myobjects = [Obj(0), Obj(1), Obj(2), Obj(3), Obj(4), Obj(5), Obj(6)]
go_to_end(
    graph={
        myobjects[3]: myobjects[1],
        myobjects[1]: myobjects[2],
        myobjects[2]: myobjects[5],
        myobjects[5]: myobjects[6],
    },
    start=myobjects[3],
)
```




    self.value = 6



... because this comparison is truthy ...


```python
myobjects[0] == myobjects[0]
```




    True



This, on the other hand, goes nowhere ...


```python
go_to_end(
    graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
    start=Obj(3),
)
```




    self.value = 3



... because this comparison is not ...


```python
Obj(3) == Obj(3)
```




    False



This occurs because the default `__hash__` and `__eq__` methods use `id(self)`.
The comparison by default is not based on the objects data, it's based on whether the objects *are actually the same reference*.

Further fun complications arise because a dataclass (quite sensibly) overrides this behaviour and is therefore not hashable by default.


```python
from dataclasses import dataclass

@dataclass
class Obj:
    value: int

go_to_end(
    graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
    start=Obj(3),
)
```


    ---------------------------------------------------------------------------

    TypeError                                 Traceback (most recent call last)

    <ipython-input-12-98273397860d> in <module>
          6 
          7 go_to_end(
    ----> 8     graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
          9     start=Obj(3),
         10 )


    TypeError: unhashable type: 'Obj'


However we do get an equality comparator by default.


```python
Obj(3) == Obj(3)
```




    True



The below code, however, works as intended.
`frozen=True` signals that the object should build its own `__hash__` method, which basically means make a tuple of all the data members in order and hash that (all data members must be hashable for this to work).


```python
@dataclass(frozen=True)
class Obj:
    value: int

go_to_end(
    graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
    start=Obj(3),
)
```




    Obj(value=6)



This language feature is a bit odd when coming over from C++, since everything in C++ land is neither hashable nor comparable unless you're really explicit about it.

## Cost of `__hash__` and `__eq__`

This is basically what the dataclass is doing under the hood, with some print statements to show the call chain.


```python
def go_to_end_loudly(graph, start):
    """ Traverse a graph. """
    print("=== START ===")
    while True:
        next_ = graph.get(start)
        if next_ is None:
            break
        print("=== STEP ===")
        start = next_
    print("=== STOP ===")
    return start

class Obj:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Obj(value={self.value})"
    def __hash__(self):
        print(f"Hash {self}")
        return hash(self.value,)
    def __eq__(self, other):
        print(f"Compare {self} with {other}")
        return self.value == other.value

go_to_end_loudly(
    graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
    start=Obj(3),
)
```

    Hash Obj(value=3)
    Hash Obj(value=1)
    Hash Obj(value=2)
    Hash Obj(value=5)
    === START ===
    Hash Obj(value=3)
    Compare Obj(value=3) with Obj(value=3)
    === STEP ===
    Hash Obj(value=1)
    Compare Obj(value=1) with Obj(value=1)
    === STEP ===
    Hash Obj(value=2)
    Compare Obj(value=2) with Obj(value=2)
    === STEP ===
    Hash Obj(value=5)
    Compare Obj(value=5) with Obj(value=5)
    === STEP ===
    Hash Obj(value=6)
    === STOP ===





    Obj(value=6)



At each step in the algorithm, using the object as a key to look up its next neighbour requires first hashing it, then performing an equality check (you'll get multiple equality checks if there are hash collisions, but that's fairly unlikely if you let `dataclass` handle things).
If your hash function is expensive (like if your dataclass is big), then using it for frequent lookups will start to get very slow.

Ensuring your class doesn't define `__eq__` or `__hash__` is one option, then they'll be compared and hashed by `id(self)`.
IMO this is risky; while you can rely on the behaviour, you have to watch out for:

* inadvertently using an object with an expensive `__hash__` method, and
* attempting to look up one object using another with identical data where in fact they don't match.

It's likely clearer and faster to construct your own identifiers for things like index -> variable object mappings.

## Nice uses of hashable objects

Here are some cases where the hashable property of dataclasses is both handy and efficient.

**Whittling out duplicates of complex objects**


```python
@dataclass(frozen=True)
class SomeProperty:
    value1: int
    value2: int

data = [
    SomeProperty(1, 3),
    SomeProperty(2, 2),
    SomeProperty(1, 3),
    SomeProperty(2, 2),
    SomeProperty(1, 3),
    SomeProperty(3, 2),
]

set(data)
```




    {SomeProperty(value1=1, value2=3),
     SomeProperty(value1=2, value2=2),
     SomeProperty(value1=3, value2=2)}



**Counting occurences of complex objects**


```python
from collections import Counter

Counter(data)
```




    Counter({SomeProperty(value1=1, value2=3): 3,
             SomeProperty(value1=2, value2=2): 2,
             SomeProperty(value1=3, value2=2): 1})



**Calculating some summary statistic based on a complicated comparison key**


```python
from collections import defaultdict

# These entries could also be a dataclass... but you only
# want to make the comparison key bit hashable so keep that
# as its own class.
data = [
    {"property": SomeProperty(1, 3), "value": 0.1},
    {"property": SomeProperty(2, 2), "value": 0.2},
    {"property": SomeProperty(1, 3), "value": 0.3},
    {"property": SomeProperty(2, 2), "value": 0.4},
    {"property": SomeProperty(1, 3), "value": 0.5},
    {"property": SomeProperty(3, 2), "value": 0.6},
]

result = defaultdict(lambda: 0)
for entry in data:
    result[entry["property"]] += entry["value"]
result
```




    defaultdict(<function __main__.<lambda>()>,
                {SomeProperty(value1=1, value2=3): 0.9,
                 SomeProperty(value1=2, value2=2): 0.6000000000000001,
                 SomeProperty(value1=3, value2=2): 0.6})



## Bad behaviour

Here's what happens if you screw up the hash computation (this one returns the same hash for every object)... the dict has to fall back on open addressing equality checks because hashes don't separate things into sensible buckets anymore. It just compares things in sequence until it gets a match. This is the silent killer...


```python
class Obj:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Obj(value={self.value})"
    def __hash__(self):
        print(f"Hash {self}")
        return 0                  # BAAAAAAAAAAD
    def __eq__(self, other):
        print(f"Compare {self} with {other}")
        return self.value == other.value

go_to_end_loudly(
    graph={Obj(3): Obj(1), Obj(1): Obj(2), Obj(2): Obj(5), Obj(5): Obj(6)},
    start=Obj(3),
)
```

    Hash Obj(value=3)
    Hash Obj(value=1)
    Compare Obj(value=3) with Obj(value=1)
    Hash Obj(value=2)
    Compare Obj(value=3) with Obj(value=2)
    Compare Obj(value=1) with Obj(value=2)
    Hash Obj(value=5)
    Compare Obj(value=3) with Obj(value=5)
    Compare Obj(value=1) with Obj(value=5)
    Compare Obj(value=2) with Obj(value=5)
    === START ===
    Hash Obj(value=3)
    Compare Obj(value=3) with Obj(value=3)
    === STEP ===
    Hash Obj(value=1)
    Compare Obj(value=3) with Obj(value=1)
    Compare Obj(value=1) with Obj(value=1)
    === STEP ===
    Hash Obj(value=2)
    Compare Obj(value=3) with Obj(value=2)
    Compare Obj(value=1) with Obj(value=2)
    Compare Obj(value=2) with Obj(value=2)
    === STEP ===
    Hash Obj(value=5)
    Compare Obj(value=3) with Obj(value=5)
    Compare Obj(value=1) with Obj(value=5)
    Compare Obj(value=2) with Obj(value=5)
    Compare Obj(value=5) with Obj(value=5)
    === STEP ===
    Hash Obj(value=6)
    Compare Obj(value=3) with Obj(value=6)
    Compare Obj(value=1) with Obj(value=6)
    Compare Obj(value=2) with Obj(value=6)
    Compare Obj(value=5) with Obj(value=6)
    === STOP ===





    Obj(value=6)




```python

```
