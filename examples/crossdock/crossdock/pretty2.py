from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import (
    Hashable,
    NewType,
    Tuple,
    List,
    Mapping,
    Any,
    Iterable,
    FrozenSet,
    TypeVar,
    Generic,
    Type,
)

"""
Data specification (pretty simple).
"""

Location = Hashable
LocationPair = Tuple[Location, Location]


@dataclass
class Warehouse:
    location: Location
    demand_locations: List[Location]


@dataclass
class CrossDockInstance:
    dock_location: Location
    warehouses: List[Warehouse]
    travel_distance: Mapping[LocationPair, float]

    @cached_property
    def all_demand_locations(self) -> FrozenSet[Location]:
        return frozenset(
            chain(*(warehouse.demand_locations for warehouse in self.warehouses))
        )


"""
Some general utility stuff needed to achieve the below.
"""

import gurobipy

BinaryVar = str


class BinaryVarSet:
    def __init__(self, gurobi_model):
        self.gurobi_model = gurobi_model
        self.created_variables = {}

    def __getitem__(self, key: LocationPair) -> BinaryVar:
        if variable := self.created_variables.get(key):
            return variable
        variable = self.gurobi_model.addVar(vtype=gurobipy.GRB.BINARY)
        self.created_variables[key] = variable
        return variable

    def items(self) -> Iterable[Tuple[LocationPair, BinaryVar]]:
        return self.created_variables.items()


class ModelBuilder:
    def __init__(self):
        self.gurobi_model = gurobipy.Model()

    def binary_variable(self) -> BinaryVar:
        return self.gurobi_model.addVar(vtype=gurobipy.GRB.BINARY)

    def binary_variable_set(self) -> BinaryVarSet:
        return BinaryVarSet(self.gurobi_model)

    def constraint(self, expressions) -> None:
        pass

    def build(self):
        pass


"""
Helper class captures some of the problem structure.
"""


@dataclass
class DemandNode:

    instance: CrossDockInstance
    warehouse: Warehouse
    location: Location

    truck: Truck

    def demand_inflows_before_dock(self) -> Iterable[BinaryVar]:
        yield self.truck.arcs_before_dock[self.truck.warehouse.location, self.location]
        yield from (
            self.truck.arcs_before_dock[other, self.location]
            for other in self.truck.warehouse.demand_locations
            if other != self.location
        )

    def demand_outflows_before_dock(self) -> Iterable[BinaryVar]:
        yield self.truck.arcs_before_dock[self.location, self.instance.dock_location]
        yield from (
            self.truck.arcs_before_dock[self.location, other]
            for other in self.truck.warehouse.demand_locations
            if other != self.location
        )

    def demand_inflows_after_dock(self) -> Iterable[BinaryVar]:
        yield self.truck.arcs_before_dock[self.instance.dock_location, self.location]
        yield from (
            self.truck.arcs_before_dock[other, self.location]
            for other in self.instance.all_demand_locations
            if other != self.location
        )

    def demand_outflows_after_dock(self) -> Iterable[BinaryVar]:
        pass


@dataclass
class Truck:

    instance: CrossDockInstance
    warehouse: Warehouse

    visits_dock: BinaryVar
    arcs_before_dock: BinaryVarSet
    arcs_after_dock: BinaryVarSet

    def warehouse_outflows(self) -> Iterable[BinaryVar]:
        yield from (
            self.arcs_before_dock[self.warehouse.location, location]
            for location in self.warehouse.demand_locations
        )
        yield self.arcs_before_dock[
            self.warehouse.location, self.instance.dock_location
        ]

    def warehouse_inflows(self) -> Iterable[BinaryVar]:
        yield from (
            self.arcs_before_dock[location, self.warehouse.location]
            for location in self.warehouse.demand_locations
        )
        yield from (
            self.arcs_after_dock[location, self.warehouse.location]
            for location in self.instance.all_demand_locations
        )
        yield self.arcs_after_dock[self.instance.dock_location, self.warehouse.location]

    def dock_inflows(self) -> Iterable[BinaryVar]:
        pass

    def dock_outflows(self) -> Iterable[BinaryVar]:
        pass


def formulate_model(instance):

    model = ModelBuilder()

    trucks = [
        Truck(
            instance=instance,
            warehouse=warehouse,
            visits_dock=model.binary_variable(),
            arcs_before_dock=model.binary_variable_set(),
            arcs_after_dock=model.binary_variable_set(),
        )
        for warehouse in instance.warehouses
    ]

    # Flows conserved.
    model.constraint(sum(truck.warehouse_outflows()) == 1 for truck in trucks)
    model.constraint(sum(truck.warehouse_inflows()) == 1 for truck in trucks)
    model.constraint(sum(truck.dock_inflows()) == truck.visits_dock for truck in trucks)
    model.constraint(
        sum(truck.dock_outflows()) == truck.visits_dock for truck in trucks
    )
    model.constraint(
        sum(node.inflows_before_dock()) == sum(node.outflows_before_dock())
        for truck in trucks
        for node in truck.demand_nodes
    )
    model.constraint(
        sum(node.inflows_after_dock()) == sum(node.outflows_after_dock())
        for truck in trucks
        for node in truck.demand_nodes
    )

    # Demand served.
    model.constraint(
        sum(node.inflows_before_dock())
        + sum(node.inflows_after_dock()) * truck.visits_dock
        == 1
        for truck in trucks
        for node in truck.demand_nodes
    )

    return model.build()
