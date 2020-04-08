"""
Repeatable things that might be useful?

TODO something to squash gurobi's output because it gets in the way
     of pytest output
TODO a require() decorator that transparently handles generators
     without consuming their contents
"""

import logging

logger = logging.getLogger(__name__)


def solve_wrapper(gurobi_model, *, callbacks, **params):
    """ Allows callbacks to be defined using a mapping from the gurobi where
    value to a callable which takes the model. Sets parameters in the model
    and runs the optimiser. If the callback raises an exception, terminates
    the solve and re-raises. """

    callback_exception = None

    def callback(cb_model, where):
        if where in callbacks:
            try:
                callbacks[where](cb_model)
            except Exception as e:
                logger.exception("Failure in callback. Terminating solve.")
                cb_model.terminate()
                nonlocal callback_exception
                callback_exception = e

    for param, value in params.items():
        if value is not None:
            setattr(gurobi_model.params, param, value)

    gurobi_model.optimize(callback)
    if callback_exception is not None:
        logger.error("Solve was interrupted by a callback failure.")
        raise callback_exception
