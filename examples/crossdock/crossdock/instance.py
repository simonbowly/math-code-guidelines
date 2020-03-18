""" Problem instance and solution classes, random problem generator. """

import json
from dataclasses import dataclass, field
from itertools import chain
from math import sqrt
from random import Random
from typing import Dict, FrozenSet, List, Tuple


__all__ = ["read_json", "generate_random_instance"]


@dataclass
class CrossDockInstance:
    """
    points: x, y coordinate pairs
    crossdock_node: point index giving the dock location
    warehouse_nodes: point index giving the dock location
    demand_nodes: for each warehouse, list of points it must deliver to

    TODO add dock/no-dock constraints at the instance level, so that the
    quadratic constraints are never realised if dock variables are fixed
    TODO add a decompose() method which creates the component subproblems
    TODO don't make variables for redundant arcs (skip all post- arcs if a
    truck is forced to skip the dock, only make pre-arcs for nodes with
    demand from the given warehouse)
    """

    warehouse_demand: Dict[int, List[int]]
    distances: None = field(repr=False)

    def __post_init__(self):
        assert self.crossdock_node not in self.warehouse_demand.keys()
        assert all(
            self.crossdock_node not in nodes
            and all(w not in nodes for w in self.warehouse_demand.keys())
            for nodes in self.warehouse_demand.values()
        )

    @property
    def crossdock_node(self):
        return 0

    @property
    def warehouse_nodes(self):
        return self.warehouse_demand.keys()

    @property
    def all_nodes(self) -> FrozenSet[int]:
        return frozenset(
            chain(
                [self.crossdock_node],
                self.warehouse_demand.keys(),
                *self.warehouse_demand.values(),
            )
        )

    @property
    def all_demand_nodes(self) -> FrozenSet[int]:
        return frozenset(chain(*self.warehouse_demand.values()))

    def distance(self, i: int, j: int) -> float:
        return self.distances.distance(i, j)

    def to_json(self, file_path, pretty=False):
        obj = {
            "warehouse_demand": self.warehouse_demand,
            "points": self.distances.points,
        }
        kwargs = {"indent": 4} if pretty else {}
        with open(file_path, "w") as outfile:
            json.dump(obj, outfile, **kwargs)


@dataclass
class EuclideanDistances:

    points: Dict[int, Tuple[float, float]]

    def distance(self, i: int, j: int) -> float:
        """ Return euclidean distance between points i and j. """
        assert i != j and i in self.points and j in self.points
        dx = self.points[i][0] - self.points[j][0]
        dy = self.points[i][1] - self.points[j][1]
        return sqrt(dx * dx + dy * dy)


@dataclass
class CrossDockSolution:

    paths: None

    def path_repr(self, wnode):
        return " -> ".join(
            "C" if node == 0 else "W" if node == wnode else str(node)
            for node in self.paths[wnode]
        )

    def __repr__(self):
        return "\n".join(
            [f"CrossDockSolution"]
            + [
                f"    Warehouse {warehouse_node} "
                f"Path {self.path_repr(warehouse_node)}"
                for warehouse_node, path in self.paths.items()
            ]
        )


def read_json(file_path):
    with open(file_path) as infile:
        obj = json.load(infile)
    return CrossDockInstance(
        warehouse_demand={
            int(warehouse): demand
            for warehouse, demand in obj["warehouse_demand"].items()
        },
        distances=EuclideanDistances(
            {int(label): tuple(point) for label, point in obj["points"].items()}
        ),
    )


def generate_random_instance(seed: int, npoints: int, nwarehouses: int):
    rstate = Random(seed)
    points = {i: (rstate.uniform(0, 1), rstate.uniform(0, 1)) for i in range(npoints)}
    distances = EuclideanDistances(points)
    crossdock_node = 0
    warehouse_nodes = list(range(1, nwarehouses + 1))
    nodes = list(range(nwarehouses + 1, npoints))
    demand_nodes = [
        rstate.sample(nodes, (npoints - nwarehouses - 1) // 2)
        for _ in range(nwarehouses)
    ]
    return CrossDockInstance(
        distances=distances, warehouse_demand=dict(zip(warehouse_nodes, demand_nodes))
    )
