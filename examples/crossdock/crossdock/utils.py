"""
Repeatable things that might be useful?

TODO something to squash gurobi's output because it gets in the way
     of pytest output
TODO a require() decorator that transparently handles generators
     without consuming their contents
"""

import functools
import gzip
import json
import logging

import wrapt


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
                logging.exception("Failure in callback. Terminating solve.")
                cb_model.terminate()
                nonlocal callback_exception
                callback_exception = e

    for param, value in params.items():
        if value is not None:
            setattr(gurobi_model.params, param, value)

    gurobi_model.optimize(callback)
    if callback_exception is not None:
        logging.error("Solve was interrupted by a callback failure.")
        raise callback_exception


def decorate_json_writer(filepath_or_buffer, pretty=False):
    pass


@wrapt.decorator(adapter=decorate_json_writer)
def json_writer(wrapped, instance, args, kwargs):
    def execute(filepath, pretty=False, compress=False):
        obj = wrapped()
        if compress:
            with gzip.open(filepath, "wt", encoding="utf-8") as outfile:
                json.dump(obj, outfile)
        else:
            dump_kwargs = {"indent": 4} if pretty else {}
            with open(filepath, "w") as outfile:
                json.dump(obj, outfile, **dump_kwargs)

    execute(*args, **kwargs)


def decorate_json_reader(filepath_or_buffer):
    pass


@wrapt.decorator(adapter=decorate_json_reader)
def json_reader(wrapped, instance, args, kwargs):
    def execute(filepath):
        if str(filepath).endswith(".gz"):
            open_ = functools.partial(gzip.open, mode="rt", encoding="utf-8")
        else:
            open_ = open
        with open_(filepath) as infile:
            obj = json.load(infile)
        return wrapped(obj)

    return execute(*args, **kwargs)
