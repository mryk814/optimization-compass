HORIZON = 20
DECAY = 0.92
DT = 0.1
TARGET = 1.0
CONTROL_PENALTY = 0.002
LEARNING_RATE = 4.0


def rollout(controls: list[float]) -> list[float]:
    states = [0.0]
    for control in controls:
        states.append(DECAY * states[-1] + DT * control)
    return states


def objective(controls: list[float]) -> tuple[float, list[float]]:
    states = rollout(controls)
    terminal_cost = (states[-1] - TARGET) ** 2
    control_cost = CONTROL_PENALTY * sum(control * control for control in controls)
    return terminal_cost + control_cost, states


controls = [0.0] * HORIZON
terminal_weights = [
    DT * DECAY ** (HORIZON - 1 - index)
    for index in range(HORIZON)
]
history = []
for iteration in range(81):
    cost, states = objective(controls)
    history.append((iteration, cost, states[-1]))
    if iteration == 80:
        break

    terminal_error = states[-1] - TARGET
    gradient = [
        2.0 * terminal_error * weight + 2.0 * CONTROL_PENALTY * control
        for weight, control in zip(terminal_weights, controls, strict=True)
    ]
    controls = [
        max(-1.0, min(1.0, control - LEARNING_RATE * derivative))
        for control, derivative in zip(controls, gradient, strict=True)
    ]

print(history[0], history[-1])
print(sum(control >= 1.0 - 1e-12 for control in controls))
