"""Quick run of the physics evolver — small enough to finish, big enough to mean something."""

from evolving_physics import PhysicsEvolver

evolver = PhysicsEvolver(
    population_size=20,
    world_size=(25, 25),
    sim_steps=150,
    fitness_goal='complexity',
    num_trials=2
)

result = evolver.run(num_generations=15, verbose=True)

# Summary
print()
if result['hall_of_fame']:
    best_rule = result['hall_of_fame'][0][1]
    best_fitness = result['hall_of_fame'][0][0]
    print(f"Best physics found: {best_rule} (fitness {best_fitness:.4f})")
    print(f"Total unique rules in hall of fame: {len(result['hall_of_fame'])}")