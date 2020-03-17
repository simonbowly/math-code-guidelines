"""
The first few tests here are property-based tests: given random data, construct an
expected input and output and verify the function result.
The last test is a fuzz test: throw random data at the function that it should be
able to handle, and let the functions internal asserts do the testing.
"""

from itertools import chain

from hypothesis import assume, given, settings
from hypothesis.strategies import lists, integers, tuples, just

from crossdock.algorithms import get_subtours, path_from_edges, single_tour_heuristic
from .test_instance import st_instance_euclidean


@given(
    lists(integers(max_value=-1), unique=True),
    lists(integers(min_value=1), unique=True),
)
def test_get_subtours(loop, not_loop):
    """ Construct edges by including one loop and one path. Check that the
    loop is returned. """
    edges = list(zip(not_loop, not_loop[1:])) + list(zip(loop, loop[1:] + loop[:1]))
    subtours = get_subtours(edges)
    if loop:
        assert len(subtours) == 1
        (subtour,) = subtours
        assert set(subtour) == set(loop)
    else:
        assert not subtours


@given(lists(integers(), min_size=2, unique=True))
def test_path_from_edges(order):
    """ After turning a path into edges, path_from_edges() should recover the order. """
    edges = list(zip(order, order[1:]))
    assert path_from_edges(edges, start=order[0]) == order


@given(
    lists(integers(), min_size=10, unique=True).flatmap(
        lambda order: tuples(
            just(order), integers(min_value=0, max_value=len(order) - 1)
        )
    )
)
def test_path_from_edges_loop(arg):
    """ Create a loop, reduce it to its component edges, check that the
    algorithm recovers the path when it starts from some point in the loop.
    """
    order, split = arg
    edges = list(zip(order, order[1:] + order[:1]))
    assert path_from_edges(edges, start=order[split]) == (
        order[split:] + order[:split] + [order[split]]
    )


@given(st_instance_euclidean)
def test_single_tour_heuristic(instance):
    """ Just throw test cases at the algorithm and rely on its internal assertions
    to check that it works as planned. """
    single_tour_heuristic(instance)
