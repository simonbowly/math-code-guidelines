""" Problem instance and solution classes, random problem generator. """

import json
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from math import sqrt
from random import Random
from typing import Any, Dict, FrozenSet, List, Tuple

from .utils import json_reader, json_writer


__all__ = ["read_json", "generate_random_instance"]


@dataclass
class CrossDockInstance:

    warehouse_demand: Dict[int, List[int]]
    distances: Any

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

    @cached_property
    def all_nodes(self) -> FrozenSet[int]:
        return frozenset(
            chain(
                [self.crossdock_node],
                self.warehouse_demand.keys(),
                *self.warehouse_demand.values(),
            )
        )

    @cached_property
    def all_demand_nodes(self) -> FrozenSet[int]:
        return frozenset(chain(*self.warehouse_demand.values()))

    def distance(self, i: int, j: int) -> float:
        return self.distances.distance(i, j)

    @json_writer
    def to_json(self):
        return {
            "warehouse_demand": [
                {"warehouse": warehouse, "demand_nodes": demand_nodes}
                for warehouse, demand_nodes in self.warehouse_demand.items()
            ],
            "distance": self.distances.to_dict(),
        }


@dataclass
class EuclideanDistances:

    points: Dict[int, Tuple[float, float]] = field(repr=False)

    def to_dict(self):
        return {
            "type": "euclidean_2d",
            "points": [
                {"label": label, "point": point} for label, point in self.points.items()
            ],
        }

    def distance(self, i: int, j: int) -> float:
        """ Return euclidean distance between points i and j. """
        assert i != j and i in self.points and j in self.points
        dx = self.points[i][0] - self.points[j][0]
        dy = self.points[i][1] - self.points[j][1]
        return sqrt(dx * dx + dy * dy)


@dataclass
class ExplicitDistances:

    matrix: Dict[Tuple[int, int], float]

    def distance(self, i: int, j: int) -> float:
        return self.matrix[i, j]


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


def read_distances(obj):
    if obj["type"] == "euclidean_2d":
        return EuclideanDistances(
            {entry["label"]: tuple(entry["point"]) for entry in obj["points"]}
        )


@json_reader
def read_json(obj):
    return CrossDockInstance(
        warehouse_demand={
            entry["warehouse"]: entry["demand_nodes"]
            for entry in obj["warehouse_demand"]
        },
        distances=read_distances(obj["distance"]),
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
