""" Some useful algorithms independent of the MIP models. Contracts are specified
using require/ensure, which allows randomised tests to find errors and will fail
if other code tries to use it incorrectly (in debug mode at least). """

from typing import List, Tuple

from icontract import require, ensure


def unique(gen):
    """ For testing. Don't worry about efficiency, just make sure it doesn't
    alter its input arguments. """
    elements = list(gen)
    return len(set(elements)) == len(elements)


@require(lambda edges: unique(in_ for in_, out in edges))
@require(lambda edges: unique(out for in_, out in edges))
def get_subtours(edges: List[Tuple[int, int]]) -> List[List[int]]:
    """ Given a list of directed edges, return a list of closed loops.
    Requires that there is only one input and one output edge per node. """
    graph = dict(edges)
    current = None
    remaining = set(graph)
    result = []
    while remaining:
        if current is None:
            subtour = []
            current = next(iter(remaining))
        if current in remaining:
            subtour.append(current)
            remaining.remove(current)
            current = graph[current]
        else:
            # Skip open paths.
            current = None
        if current == subtour[0]:
            current = None
            result.append(subtour)
    assert not remaining
    return result


def no_sub_loops(edges):
    """ Condition passes if there are no cycles or the edges make one
    big cycle. """
    subtours = get_subtours(edges)
    if not subtours:
        return True
    if len(subtours) == 1 and len(subtours[0]) == len(edges):
        return True
    return False


@require(lambda edges: unique(in_ for in_, out in edges))
@require(lambda edges: unique(out for in_, out in edges))
@require(no_sub_loops)
@require(lambda edges, start: any(arc[0] == start for arc in edges))
@ensure(lambda edges, result: len(result) == len(edges) + 1)
@ensure(lambda result: unique(result[:-1]))
def path_from_edges(edges, start):
    """ Given a collection of unique arcs, find the path beginning with start
    which consumes all arcs in the set. Fails if there are cycles or the arc
    set does not represent a single path. """
    current = start
    path = [current]
    arcset = {tuple(arc) for arc in edges}
    while arcset:
        arc = next(arc for arc in arcset if arc[0] == current)
        arcset.remove(arc)
        current = arc[1]
        path.append(current)
    assert not arcset
    return path


def single_tour_heuristic(instance):
    """ Return an ordering of the demand nodes from the crossdock, finishing at
    the first warehouse, so that one truck can do the rounds. Uses a min distance
    constructive heuristics followed by 2-opt local search.
    TODO finish and integrate this as a start heuristic.
    """

    order = [instance.crossdock_node()]
    remaining = set(instance.all_demand_nodes())
    while remaining:
        next_node = min(remaining, key=lambda n: instance.distance(order[-1], n))
        remaining.remove(next_node)
        order.append(next_node)
    order.append(next(iter(instance.warehouse_nodes())))

    def open_path_cost(order):
        return sum(instance.distance(i, j) for i, j in zip(order, order[1:]))

    def neighbours(order):
        for start in range(1, len(order)):
            for end in range(start + 2, len(order)):
                new_order = (
                    order[:start] + list(reversed(order[start:end])) + order[end:]
                )
                assert (
                    len(new_order) == len(order)
                    and new_order[0] == order[0]
                    and new_order[-1] == order[-1]
                )
                yield new_order

    def local_step(order):
        cost = open_path_cost(order)
        best_neighbour = min(neighbours(order), key=open_path_cost)
        best_step_cost = open_path_cost(best_neighbour)
        return best_neighbour if best_step_cost < cost else order

    def local_search(order):
        while True:
            new_order = local_step(order)
            if new_order == order:
                return order
            order = new_order

    return local_search(order)
