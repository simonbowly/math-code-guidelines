
# Crossdock example

Crossdocking routes trucks from warehouses to demand nodes, optionally
via a crossdock.
Trucks can service demand from their own warehouses before they visit the crossdock, or from any warehouse after the visit the dock.
It's highly contrived (no timings, etc) but it's got a callback (and a heuristic and parallel decomposition when I get around to it).

This is still a bit rough (ugly code, and I don't think the algorithms I've written in here are very efficient) this is more meant to be an example of structuring the code and writing useful tests.
Work in progress!
Also, I'm most likely going to break some of my own rules ... I figure we aim to collect and adapt examples and adjust the rules until we land on a workable set of guidelines.

For file heirarchy, follow the python package setup.
There's no need for a `setup.py` file, at least until you need to call the code from outside this directory (tests should run fine without installing the module).
Include `__init__.py` files so that things are treated as modules and you can do relative imports.

```
README.md
    |- crossdock
        |- __init__.py
        |- algorithms.py    # Utility algorithms indepdendent of Gurobi stuff.
        |- instance.py      # Specification/objects representing a problem instance.
        |- model.py         # Everything related to Gurobi modelling.
        |- utils.py         # Stuff with utility.
    |- tests
        |- __init__.py
        |- test_algorithms.py
        |- test_instance.py
        |- test_model.py
    |- scripts
        |- simple.py        # Script generates and solves seeded random model.
```

* Run `python -O scripts/simple.py` to run a test problem (optimised flag drops the pre- and post-condition checks run by icontract).
* Run `pytest --cov crossdock` to run tests and get module-level coverage info.

# Testing

Running the fuzztests in this model caught that I'd allowed the model to make multiple visits to the same demand node which I had not intended.
In practice these are always sub-optimal, but it did catch an error in my solution processor where it assumed a truck would never make redundant visits.
The error cases were detected because hypothesis likes to throw edges cases at your code (in this case a bunch of zero distance matrices).
