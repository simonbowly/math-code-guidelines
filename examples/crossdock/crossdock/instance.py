""" Problem instance and solution classes, random problem generator. """

import json
from collections import defaultdict
from functools import lru_cache
from itertools import chain
from math import sqrt
from random import Random
from typing import Dict, FrozenSet, List, Tuple


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

    def __init__(self, warehouse_demand: Dict[int, List[int]], distances):
        self._crossdock_node = 0
        assert self._crossdock_node not in warehouse_demand.keys()
        assert all(
            self._crossdock_node not in nodes
            and all(w not in nodes for w in warehouse_demand.keys())
            for nodes in warehouse_demand.values()
        )
        self._warehouse_demand = warehouse_demand
        self._distances = distances

    def __repr__(self):
        return (
            "CrossDockInstance("
            f"crossdock={self.crossdock_node()}, "
            f"warehouses={self.warehouse_demand()})"
        )

    def crossdock_node(self):
        return self._crossdock_node

    def warehouse_nodes(self):
        return self._warehouse_demand.keys()

    def warehouse_demand(self):
        return self._warehouse_demand

    @lru_cache()
    def all_nodes(self) -> FrozenSet[int]:
        return frozenset(
            chain(
                [self._crossdock_node],
                self._warehouse_demand.keys(),
                *self._warehouse_demand.values(),
            )
        )

    @lru_cache()
    def all_demand_nodes(self) -> FrozenSet[int]:
        return frozenset(chain(*self._warehouse_demand.values()))

    def distance(self, i: int, j: int) -> float:
        return self._distances.distance(i, j)


class EuclideanDistances:
    def __init__(self, points: Dict[int, Tuple[float, float]]):
        self.points = points

    def distance(self, i: int, j: int) -> float:
        """ Return euclidean distance between points i and j. """
        assert i != j and i in self.points and j in self.points
        dx = self.points[i][0] - self.points[j][0]
        dy = self.points[i][1] - self.points[j][1]
        return sqrt(dx * dx + dy * dy)


class CrossDockSolution:
    def __init__(self, instance, paths):
        self.instance = instance
        self.paths = paths

    @lru_cache()
    def cost(self, wnode):
        return sum(
            self.instance.distance(i, j)
            for i, j in zip(self.paths[wnode], self.paths[wnode][1:])
        )

    @lru_cache()
    def path_repr(self, wnode):
        return " -> ".join(
            "C" if node == 0 else "W" if node == wnode else str(node)
            for node in self.paths[wnode]
        )

    @lru_cache()
    def total_cost(self):
        return sum(self.cost(wnode) for wnode in self.instance.warehouse_demand())

    def __repr__(self):
        return "\n".join(
            [f"CrossDockSolution(cost={self.total_cost():.2f})"]
            + [
                f"    Warehouse {warehouse_node} "
                f"(Cost {self.cost(warehouse_node):.2f}) "
                f"Path {self.path_repr(warehouse_node)}"
                for warehouse_node, path in self.paths.items()
            ]
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
