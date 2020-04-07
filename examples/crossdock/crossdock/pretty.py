from dataclasses import dataclass
from functools import partial
from itertools import chain, combinations
from typing import Any, List, Mapping, Tuple


@dataclass
class Warehouse:
    location: Any
    demand_locations: List[Any]


@dataclass
class CrossDockInstance:
    warehouses: List[Warehouse]
    distance: Mapping[Tuple[Any, Any], float]


# Build up an attached model.

import gurobipy


@dataclass
class WarehouseVars:  # Should be a truck really?
    """ This is a bad example because I don't need :d at all after I've set
    up the objective ... """

    d: Warehouse
    visits_dock: BinaryVar
    travel_before_dock: Mapping[Tuple[Any, Any], BinaryVar]
    travel_after_dock: Mapping[Tuple[Any, Any], BinaryVar]

    def inflows_before_dock(self, location):
        yield self.d.location
        yield from (other for other in self.d.demand_locations if other != location)


@dataclass
class Model:
    gurobi_model: Any
    warehouses: List[WarehouseVars]


gurobi_model = gurobipy.Model()


pairwise = partial(combinations, r=2)
binary_variable = partial(gurobi_model.addVar, vtype=gurobipy.GRB.BINARY)

model = Model(
    gurobi_model=gurobi_model,
    warehouses=[
        WarehouseVars(
            d=warehouse,
            visits_dock=binary_variable(obj=0),
            travel_before_dock={
                (i, j): binary_variable(obj=instance.distance[i, j])
                for i, j in pairwise(
                    chain(
                        [instance.crossdock_location, warehouse.location],
                        warehouse.demand_locations,
                    )
                )
            },
            travel_after_dock={
                (i, j): binary_variable(obj=instance.distance[i, j])
                for i, j in pairwise(
                    chain(
                        [instance.crossdock_location, warehouse_location],
                        instance.all_demand_nodes(),
                    )
                )
            },
        )
        for warehouse in instance.warehouses
    ],
)


LocationID = NewType("LocationID", Hashable)
LocationIDPair = Tuple[LocationID, LocationID]
BinaryVar = gurobipy.Var


class Truck:

    d: TruckDataWrapper

    arcs_before_dock: Mapping[LocationIDPair, BinaryVar]
    arcs_after_dock: Mapping[LocationIDPair, BinaryVar]
    visits_crossdock: BinaryVar

    @property
    def warehouse_outflows(self) -> Iterable[BinaryVar]:
        yield self.arcs_before_dock[
            self.d.warehouse_location, self.d.crossdock_location
        ]
        yield from (
            self.arcs_before_dock[self.d.warehouse_location, demand_location]
            for demand_location in self.d.my_demand_locations
        )

    @property
    def warehouse_inflows(self) -> Iterable[BinaryVar]:
        """ We can return from our demand locations directly without visiting the
        dock, from the dock, or from any location after visiting the dock. """
        yield from (
            self.arcs_before_dock[demand_location, self.d.warehouse_location]
            for demand_location in self.d.my_demand_locations
        )
        yield self.arcs_after_dock[self.d.crossdock_location]
        yield from (
            self.arcs_after_dock[demand_location, self.d.warehouse_location]
            for demand_location in self.d.all_demand_locations
        )

    @property
    def crossdock_inflows(self) -> Iterable[BinaryVar]:
        """ We can reach the crossdock only from the truck's warehouse or one of
        the demand locations it must serve. """
        yield self.arcs_before_dock[
            self.d.warehouse_location, self.d.crossdock_location
        ]
        yield from (
            self.arcs_before_dock[demand_location, self.d.crossdock_location]
            for demand_location in self.d.my_demand_locations
        )

    @property
    def crossdock_outflows(self) -> Iterable[BinaryVar]:
        """ We can depart the crossdock directly for this truck's warehouse or to
        any demand location (not just the ones served by this warehouse). """
        yield self.arcs_after_dock[self.d.crossdock_location, self.d.warehouse_location]
        yield from (
            self.arcs_after_dock[self.d.crossdock_location, demand_location]
            for demand_location in self.d.all_demand_locations
        )


# Procedural style.

for truck in model.trucks:
    constrain(sum(truck.warehouse_outflows) == 1)
    constrain(sum(truck.warehouse_inflows) == 1)
    constrain(sum(truck.crossdock_inflows) == truck.visits_crossdock)
    constrain(sum(truck.crossdock_outflows) == truck.visits_crossdock)
    for location in warehouse.demand_locations:
        constrain(
            sum(location.this_truck_inflows_before_dock)
            + truck.visits_crossdock * sum(location.any_inflows_after_dock)
            == 1
        )
        constrain(
            sum(location.inflows_before_dock) == sum(location.outflows_before_dock)
        )
    #     constrain(
    #         total(location.inflows_after_dock) == total(location.outflows_after_dock)
    #     )

# Declarative (JuMP) style.




constraint(quicksum(truck.warehouse_outflows) == 1 for truck in trucks)
constraint(quicksum(truck.warehouse_inflows) == 1 for truck in trucks)
