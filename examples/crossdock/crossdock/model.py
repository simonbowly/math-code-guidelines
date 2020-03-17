"""
Contains the Gurobi modelling components for solving a crossdock instance.
Public API:
    construct_model(instance) -> formulated model (gurobi model + variables)
    solve_model(model) -> solution components (arcs used + dock variables)
"""

import contextlib
import dataclasses
import functools
import itertools
import logging
import sys

import gurobipy

from .algorithms import get_subtours, path_from_edges
from .instance import CrossDockSolution
from .utils import solve_wrapper


__all__ = ["construct_model", "solve_model"]


def _initialise_variables(instance):
    """
    Construct a model with binary variables for pre- and post-dock arc variables
    for all trucks, and intermediary variables which specify whether each truck
    visits the crossdock.
    This process enumerates all possible arcs, even though there are a lot which
    will later be disallowed due to absence of demand.
    """
    model = gurobipy.Model()
    arc_variables = {
        phase: {
            k: {
                (i, j): model.addVar(
                    obj=instance.distance(i, j),
                    vtype=gurobipy.GRB.BINARY,
                    name=f"{phase}_{k}_{i}_{j}",
                )
                for i, j in itertools.permutations(instance.all_nodes(), r=2)
            }
            for k in instance.warehouse_nodes()
        }
        for phase in ["pre", "post"]
    }
    dock_variables = {
        k: model.addVar(obj=0, vtype=gurobipy.GRB.BINARY, name=f"dock_{k}")
        for k in instance.warehouse_nodes()
    }
    model.update()
    return model, arc_variables, dock_variables


def _add_flow_constraints(instance, model, arc_variables, dock_variables):
    """ Add flow constraints for all trucks at all nodes. """
    # Flow constraints for vehicles (in and out arcs balance on same truck).
    # Reducible: two phases can be handled differently - pre-dock flows
    # need only be specified for nodes with demand from k??
    for phase, phase_arc_variables in arc_variables.items():
        for phase_w_arc_variables in phase_arc_variables.values():
            for demand_node in instance.all_demand_nodes():
                model.addConstr(
                    gurobipy.quicksum(
                        phase_w_arc_variables[other, demand_node]
                        for other in instance.all_nodes()
                        if other != demand_node
                    )
                    <= 1
                )
                model.addConstr(
                    gurobipy.quicksum(
                        (
                            phase_w_arc_variables[other, demand_node]
                            - phase_w_arc_variables[demand_node, other]
                        )
                        for other in instance.all_nodes()
                        if other != demand_node
                    )
                    == 0
                )
    # Flow constraints at the crossdock (pre-ins balance post-outs).
    # Uses an intermediary variable which records whether truck k docks.
    for warehouse_node in instance.warehouse_nodes():
        dock_var_w = dock_variables[warehouse_node]
        pre_arc_w = arc_variables["pre"][warehouse_node]
        post_arc_w = arc_variables["post"][warehouse_node]
        # Use of post-dock arcs.
        for i, j in itertools.permutations(instance.all_nodes(), r=2):
            model.addConstr(post_arc_w[i, j] <= dock_var_w)
        # Dock arrivals.
        model.addConstr(
            gurobipy.quicksum(
                pre_arc_w[other, instance.crossdock_node()]
                for other in instance.all_nodes()
                if other != instance.crossdock_node()
            )
            == dock_var_w
        )
        # Dock departures.
        model.addConstr(
            gurobipy.quicksum(
                post_arc_w[instance.crossdock_node(), other]
                for other in instance.all_nodes()
                if other != instance.crossdock_node()
            )
            == dock_var_w
        )
        # Flow constraints at the warehouse node.
        # Pre-dock truck departs the warehouse.
        model.addConstr(
            gurobipy.quicksum(
                pre_arc_w[warehouse_node, other]
                for other in instance.all_nodes()
                if other != warehouse_node
            )
            == 1
        )
        # Either pre- or post-dock truck returns.
        model.addConstr(
            gurobipy.quicksum(
                (pre_arc_w[other, warehouse_node] + post_arc_w[other, warehouse_node])
                for other in instance.all_nodes()
                if other != warehouse_node
            )
            == 1
        )
    model.update()


def _add_demand_constraints(instance, model, arc_variables, dock_variables):
    """ Add constraints that require either that a truck visits a demand node
    directly from the warehouse that it has demand from, or that it is visited
    by any truck after going to the crossdock AND the truck from the appropriate
    warehouse also visits the dock. """
    # Demand served constraints.
    for warehouse_node, demand_nodes_w in instance.warehouse_demand().items():
        pre_arc_w = arc_variables["pre"][warehouse_node]
        dock_var_w = dock_variables[warehouse_node]
        for demand_node in demand_nodes_w:
            # All possible arrivals which can service this demand.
            incoming = gurobipy.quicksum(
                itertools.chain(
                    (
                        pre_arc_w[other, demand_node]
                        for other in instance.all_nodes()
                        if other != demand_node
                    ),
                    (
                        post_arc_w[other, demand_node] * dock_var_w
                        for post_arc_w in arc_variables["post"].values()
                        for other in instance.all_nodes()
                        if other != demand_node
                    ),
                )
            )
            model.addConstr(incoming == 1)
    # Disallowed arcs. Using sets properly would mean these variables can be removed.
    for warehouse_node in instance.warehouse_nodes():
        pre_arc_w = arc_variables["pre"][warehouse_node]
        post_arc_w = arc_variables["post"][warehouse_node]
        # Truck k cannot visit any !k warehouse nodes.
        no_visit = [
            node for node in instance.warehouse_nodes() if node != warehouse_node
        ]
        for node in no_visit:
            for other in instance.all_nodes():
                if node != other:
                    model.addConstr(pre_arc_w[node, other] == 0)
                    model.addConstr(pre_arc_w[other, node] == 0)
                    model.addConstr(post_arc_w[node, other] == 0)
                    model.addConstr(post_arc_w[other, node] == 0)
        # No post-dock truck should use an arc TO the crossdock.
        for other in instance.all_nodes():
            if other != instance.crossdock_node():
                model.addConstr(post_arc_w[other, instance.crossdock_node()] == 0)
        # No pre-dock truck should use an arc FROM the crossdock.
        for other in instance.all_nodes():
            if other != instance.crossdock_node():
                model.addConstr(pre_arc_w[instance.crossdock_node(), other] == 0)
    model.update()


@dataclasses.dataclass
class FullModel:
    """ Just a container. Prefer this little wrapper to attaching things to the
    gurobi model since its clear what exists where and you can't forget to attach
    something. """

    instance: None
    gurobi_model: None
    arc_variables: None
    dock_variables: None


def construct_model(instance, *, hotstart_single_tour_order=None, fix_dock_vars=None):
    """ Build Gurobi model and capture key variables to return as a structure.
    NOTE These functions do leave things in a partially built state, but I think it's
    worth splitting them out anyway so that the steps in model construction are
    clear and the code is signposted.
    """
    model, arc_variables, dock_variables = _initialise_variables(instance)
    _add_flow_constraints(instance, model, arc_variables, dock_variables)
    _add_demand_constraints(instance, model, arc_variables, dock_variables)
    # Once the full model is returned from this function, everything is consistent.
    return FullModel(
        instance=instance,
        gurobi_model=model,
        arc_variables=arc_variables,
        dock_variables=dock_variables,
    )


def extract_solution(instance, arc_variables):
    """ Process binary variables to return a list of arcs traversed in the
    solution by each warehouse/truck. """
    arcs = {
        phase: {
            k: [tuple(arc) for arc, var in w_phase_arc_variables.items() if var.X > 0.5]
            for k, w_phase_arc_variables in phase_arc_variables.items()
        }
        for phase, phase_arc_variables in arc_variables.items()
    }
    arcs = {k: (arcs["pre"][k], arcs["post"][k]) for k in arcs["pre"].keys()}
    return CrossDockSolution(
        instance,
        {
            warehouse_node: path_from_edges(pre_arcs, start=warehouse_node)
            + (path_from_edges(post_arcs, start=0)[1:] if post_arcs else [])
            for warehouse_node, (pre_arcs, post_arcs) in arcs.items()
        },
    )


def subtour_elimination_callback(model, arc_variables):
    """ Look for subtours and generate constraints which rule out the shortest.
    NOTE that this callback does not use anything other than its arguments,
    and it doesn't have to attach things to the model (it's called with partial()).
    This means it would be testable in isolation with a good mocking object for the
    gurobi model (feed values in via cbGetSolution, check the produced constraint
    by capturing cbLazy). Something worth developing?
    """
    for phase, phase_arc_var in arc_variables.items():
        for k, w_phase_arc_var in phase_arc_var.items():
            edges = [
                arc
                for arc, arc_val in model.cbGetSolution(w_phase_arc_var).items()
                if arc_val > 0.5
            ]
            subtours = get_subtours(edges)
            if subtours:
                shortest = min(subtours, key=len)
                if len(shortest) < len(edges):
                    logging.info(
                        f"Subtour elimination for length {len(shortest)} "
                        f"path (phase {phase}, warehouse {k})"
                    )
                    arcs = gurobipy.quicksum(
                        w_phase_arc_var[arc]
                        for arc in zip(shortest, shortest[1:] + shortest[:1])
                    )
                    model.cbLazy(arcs <= (len(shortest) - 1))
                    arcs = gurobipy.quicksum(
                        w_phase_arc_var[tuple(reversed(arc))]
                        for arc in zip(shortest, shortest[1:] + shortest[:1])
                    )
                    model.cbLazy(arcs <= (len(shortest) - 1))


def solve_model(model, threads=None):
    """ Given a formulated model, solve with a subtour elimination callback. Return
    the travel arcs used in the solution and values of the dock variables. """
    solve_wrapper(
        model.gurobi_model,
        callbacks={
            gurobipy.GRB.callback.MIPSOL: functools.partial(
                subtour_elimination_callback, arc_variables=model.arc_variables
            )
        },
        LazyConstraints=1,
        Threads=threads,
    )
    return extract_solution(model.instance, model.arc_variables)
