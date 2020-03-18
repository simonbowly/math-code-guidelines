import logging

import click

import crossdock.instance
import crossdock.model

logging.basicConfig(level=logging.WARNING)


@click.command()
@click.argument("file-path", type=click.Path(exists=True, dir_okay=False))
@click.option("--threads", type=int, default=None)
def run(file_path, threads):
    instance = crossdock.instance.read_json(file_path)
    model = crossdock.model.construct_model(instance)
    solution = crossdock.model.solve_model(model, threads=threads)
    click.echo(instance)
    click.echo(solution)


run()


# instance = generate_random_instance(19675, 25, 3)
# model = construct_model(instance)
# solution = solve_model(model)

# print(instance)
# print(solution)
