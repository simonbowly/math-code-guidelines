from dataclasses import dataclass

from memory_profiler import profile


@profile
def dicts():
    data = [{"value": i, "a": i * 2, "b": i * 3, "c": i * 4, "d": i * 5} for i in range(100000)]
    return sum(obj["value"] for obj in data)


@dataclass
class MyDataClass:
    value: int
    a: int
    b: int
    c: int
    d: int


@profile
def dataclasses():
    data = [MyDataClass(i, i * 2, i * 3, i * 4, i * 5) for i in range(100000)]
    return sum(obj.value for obj in data)


# class MySlotsClass:
#     __slots__ = ["value", "a", "b", "c", "d"]

#     def __init__(self, value, a, b, c, d):
#         self.value = value
#         self.a = a
#         self.b = b
#         self.c = c
#         self.d = d


# @profile
# def slotsclasses():
#     data = [MySlotsClass(i, i * 2, i * 3, i * 4, i * 5) for i in range(100000)]
#     return sum(obj.value for obj in data)


# @dataclass
# class MySlotsDataClass:
#     __slots__ = ["value", "a", "b", "c", "d"]
#     value: int
#     a: int
#     b: int
#     c: int
#     d: int


# @profile
# def slotsdataclasses():
#     data = [MySlotsDataClass(i, i * 2, i * 3, i * 4, i * 5) for i in range(100000)]
#     return sum(obj.value for obj in data)


if __name__ == "__main__":
    dicts()
    dataclasses()
    # slotsclasses()
    # slotsdataclasses()
