from hypothesis import given, settings
from itertools import cycle
import pytest

from crossdock.model import (
    _initialise_variables,
    construct_model,
    extract_solution,
    solve_model,
)
from .test_instance import st_instance_euclidean


class Var:
    def __init__(self, X):
        self.X = X


@given(st_instance_euclidean)
def test_initialise_variables(instance):
    model, arc_variables, dock_variables = _initialise_variables(instance)
    assert set(arc_variables) == {"pre", "post"}
    for phase in ["pre", "post"]:
        assert set(arc_variables[phase]) == set(instance.warehouse_nodes())
    assert set(dock_variables) == set(instance.warehouse_nodes())


@given(st_instance_euclidean)
def test_construct_model(instance):
    """ Complete fuzz test. A test at the top level like this is really helpful
    if you want to refactor the internals of the model construction. """
    construct_model(instance)


@pytest.mark.parametrize(
    "arc_variables, expected",
    [
        (
            {
                "pre": {1: {(1, 0): Var(0.9990)}},
                "post": {1: {(0, 3): Var(0.9999), (0, 4): Var(0.0001)}},
            },
            {1: [1, 0, 3]},
        ),
        # Case with no dock visit.
        (
            {
                "pre": {
                    1: {(1, 2): Var(0.9990), (2, 1): Var(0.9990), (2, 3): Var(0.0001)}
                },
                "post": {1: {(0, 3): Var(0.0001), (0, 4): Var(0.0001)}},
            },
            {1: [1, 2, 1]},
        ),
    ],
)
def test_extract_solution(arc_variables, expected):
    """ Wrote this static test specifically to help make a change in
    this single function. Bit laborious though... """
    solution = extract_solution(None, arc_variables)
    assert solution.paths == expected


@given(st_instance_euclidean.map(construct_model))
def test_solve_model(model):
    """ Throws random problems at the solver to see how it goes. Hypothesis
    produces random data in the edge-case sense, not the diverse-properties
    sense. This test (plus the various asserts) caught the fact that my code
    panicked when faced with zero distances (or potentially non-euclidean
    distances). """
    solve_model(model)
    # TODO check that various output conditions are hit by the input data
    # e.g. cases where trucks don't use the dock at all
