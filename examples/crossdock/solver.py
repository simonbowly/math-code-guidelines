import logging

import click

import crossdock.instance
import crossdock.model


LOG_LEVELS = [level.lower() for level in logging._nameToLevel if level != "NOTSET"]


def setup_console_logging(logger, level):
    # From the cookbook
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


@click.command()
@click.argument("file-path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVELS, case_sensitive=False),
    default="warning",
)
@click.option("--threads", type=int, default=None)
def run(file_path, log_level, threads):
    setup_console_logging(
        logger=logging.getLogger("crossdock"),
        level=logging._nameToLevel[log_level.upper()],
    )
    instance = crossdock.instance.read_json(file_path)
    model = crossdock.model.construct_model(instance)
    solution = crossdock.model.solve_model(model, threads=threads)
    click.echo(instance)
    click.echo(solution)


run()
