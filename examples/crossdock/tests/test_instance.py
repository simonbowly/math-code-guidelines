import io
import pathlib
import tempfile
from itertools import permutations

from hypothesis import given
from hypothesis.strategies import (
    integers,
    lists,
    tuples,
    fixed_dictionaries,
    just,
    dictionaries,
    floats,
)

from crossdock.instance import (
    CrossDockInstance,
    EuclideanDistances,
    generate_random_instance,
    read_json,
)

unit_square = tuples(
    floats(min_value=0, max_value=0, allow_nan=False, allow_infinity=False),
    floats(min_value=0, max_value=0, allow_nan=False, allow_infinity=False),
)

# This is a fun one to try and understand!!
st_instance = dictionaries(
    keys=integers(min_value=1, max_value=20),
    values=lists(integers(min_value=21), unique=True, min_size=2, max_size=3),
    min_size=1,
    max_size=3,
).map(lambda demand: CrossDockInstance(demand, None))
st_instance_euclidean = st_instance.flatmap(
    lambda instance: fixed_dictionaries(
        dict(
            demand=just(instance.warehouse_demand),
            points=fixed_dictionaries({p: unit_square for p in instance.all_nodes}),
        )
    )
).map(
    lambda data: CrossDockInstance(data["demand"], EuclideanDistances(data["points"]))
)


@given(st_instance)
def test_instance_base(instance):
    repr(instance)
    assert instance.crossdock_node == 0
    assert set(instance.warehouse_nodes) == set(instance.warehouse_demand)
    assert all(n >= 0 for n in instance.all_nodes)
    assert all(n > 20 for n in instance.all_demand_nodes)


@given(st_instance_euclidean)
def test_instance_euclidean(instance):
    for i, j in permutations(instance.all_nodes, r=2):
        assert instance.distance(i, j) >= 0


@given(
    integers(),
    integers(min_value=10, max_value=50),
    integers(min_value=1, max_value=5),
)
def test_generate_random_instance(seed, npoints, nwarehouses):
    generate_random_instance(seed, npoints, nwarehouses)


@given(st_instance_euclidean)
def test_instance_json(instance):
    with tempfile.TemporaryDirectory() as tempdir:
        file_path = pathlib.Path(tempdir).joinpath("instance.json")
        instance.to_json(file_path)
        deserialised = read_json(file_path)
    assert deserialised == instance
