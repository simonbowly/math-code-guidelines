import logging

from crossdock.instance import generate_random_instance
from crossdock.model import construct_model, solve_model


logging.basicConfig(level=logging.WARNING)

instance = generate_random_instance(19675, 25, 3)
model = construct_model(instance)
solution = solve_model(model)

print(instance)
print(solution)
