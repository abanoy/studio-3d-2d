"""Mathematical Source0x31 candidate; NOT integrated or native-client qualified.

Synthetic/reference-unit goals only. No native parsing, app APIs or SDK import.
The SDK reference was inspected, not compiled/executed. Python doubles and a
new integer fixed clock preclude any bit-exact SDK parity claim.
"""
from copy import deepcopy
from dataclasses import dataclass, replace
from types import MappingProxyType
import math

FLAGS = 0x31
FIXED_HZ = 120
DT = 1 / FIXED_HZ
ZERO = (0., 0., 0.)
IDENTITY = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))  # basis columns


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def subtract(a, b): return tuple(x - y for x, y in zip(a, b))
def multiply(a, scalar): return tuple(x * scalar for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(dot(a, a))


def vector(value):
    if len(value) != 3 or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in value):
        raise ValueError("Finite three-component vector required")
    return tuple(float(v) for v in value)


def unit(value):
    magnitude = length(value)
    if not math.isfinite(magnitude) or magnitude < 1e-12:
        raise ValueError("Degenerate direction outside candidate subset")
    return multiply(value, 1 / magnitude)


@dataclass(frozen=True)
class Parameters:
    length: float = 20.
    tip_mass: float = 20.  # native downward acceleration magnitude, not inverse mass
    yaw_stiffness: float = 50.
    yaw_damping: float = 5.
    pitch_stiffness: float = 50.
    pitch_damping: float = 5.
    angle_limit: float = 0.7853981852531433
    along_stiffness: float = 100.  # retained but inactive under length constraint
    along_damping: float = 0.
    raw_rule_flags: int = FLAGS

    def __post_init__(self):
        if type(self.raw_rule_flags) is not int or self.raw_rule_flags != FLAGS:
            raise ValueError("Only exact flexible+angle+length flags0x31 supported")
        for key, value in self.__dict__.items():
            if key == "raw_rule_flags":
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("Invalid native parameter: " + key)
        if not 1e-8 <= self.length <= 1e5 or not 0 <= self.angle_limit < math.pi / 2:
            raise ValueError("Positive bounded length and cone below90degrees required")
        if self.tip_mass > 1e6 or max(self.yaw_stiffness, self.pitch_stiffness, self.yaw_damping, self.pitch_damping) > 1e4:
            raise ValueError("Active coefficient outside mathematical prototype bounds")

    def translated_size(self, factor):
        if not isinstance(factor, (int, float)) or isinstance(factor, bool) or not math.isfinite(factor) or factor <= 0:
            raise ValueError("Positive uniform unit factor required")
        return replace(self, length=self.length * factor, tip_mass=self.tip_mass * factor)


@dataclass(frozen=True)
class Goal:
    base: tuple = ZERO
    basis: tuple = IDENTITY

    def __post_init__(self):
        object.__setattr__(self, "base", vector(self.base))
        if len(self.basis) != 3:
            raise ValueError("Three basis columns required")
        columns = tuple(vector(column) for column in self.basis)
        object.__setattr__(self, "basis", columns)
        errors = [abs(dot(columns[i], columns[j]) - (1. if i == j else 0.)) for i in range(3) for j in range(3)]
        if max(errors) > 1e-9 or dot(cross(columns[0], columns[1]), columns[2]) < 1 - 1e-9:
            raise ValueError("Positive orthonormal mathematical goal required; no mirrored/nonuniform/sheared basis")

    def tip(self, parameters):
        return add(self.base, multiply(self.basis[2], parameters.length))


@dataclass(frozen=True)
class State:
    tip: tuple
    velocity: tuple


@dataclass(frozen=True)
class Output:
    state: State
    basis: tuple
    acceleration: tuple
    unconstrained_tip: tuple
    unconstrained_velocity: tuple
    angle_projected: bool


def solve_one(parameters, goal, state, external_acceleration, gravity_down):
    """One120Hz mathematical step, called only after actor-wide validation."""
    target = goal.tip(parameters)
    error = subtract(target, state.tip)
    left, up, forward = goal.basis
    lateral = parameters.yaw_stiffness * dot(left, error) - parameters.yaw_damping * dot(left, state.velocity)
    vertical = parameters.pitch_stiffness * dot(up, error) - parameters.pitch_damping * dot(up, state.velocity)
    # Along-axis stiffness/damping are deliberately absent for flags0x31.
    acceleration = add(add(multiply(left, lateral), multiply(up, vertical)),
                       add(multiply(gravity_down, parameters.tip_mass), external_acceleration))
    velocity = add(state.velocity, multiply(acceleration, DT))
    position = add(state.tip, multiply(velocity, DT))
    unconstrained_velocity, unconstrained_tip = velocity, position
    if parameters.angle_limit == 0.:
        # The zero cone has exactly one permitted direction. Enforce that
        # analytic case before acos or normalizing a zero target difference.
        # No angular epsilon or widened tolerance is involved.
        direction = unit(forward)
        constrained = position != target
    else:
        direction = unit(subtract(position, goal.base))
        cosine = max(-1., min(1., dot(direction, forward)))
        angle = math.acos(cosine)
        if cosine < 0:
            angle = math.tau - angle
        constrained = angle > parameters.angle_limit
        if constrained:
            # Goal-tip sphere correction precedes the final fixed-length projection.
            toward_target = unit(subtract(target, position))
            position = subtract(target, multiply(toward_target, parameters.length * math.sin(parameters.angle_limit)))
            direction = unit(subtract(position, goal.base))
    position = add(goal.base, multiply(direction, parameters.length))
    velocity = subtract(velocity, multiply(direction, dot(velocity, direction)))
    out_left = unit(cross(up, direction))
    out_up = cross(direction, out_left)
    if not all(math.isfinite(v) for row in (position, velocity, acceleration, out_left, out_up, direction) for v in row):
        raise ValueError("Nonfinite mathematical result refused atomically")
    return Output(State(position, velocity), (out_left, out_up, direction), acceleration,
                  unconstrained_tip, unconstrained_velocity, constrained)


class Actor:
    """Independent rule states. Authored/hierarchical goals are caller-owned.

    No live rig or parent recomposition, collision, recording or FK application.
    Reset seeds the supplied goals at tick0; the first integration is tick1.
    Clock skips/reverse seeks require explicit reset/replay, never hidden history.
    """
    def __init__(self, parameters, raw_metadata=None, gravity_down=(0., 0., -1.)):
        if not parameters or any(not isinstance(key, str) or not isinstance(value, Parameters) for key, value in parameters.items()):
            raise ValueError("Explicit named bounded parameters required")
        self.parameters = MappingProxyType(dict(parameters))
        self.gravity_down = vector(gravity_down)
        if abs(length(self.gravity_down) - 1.) > 1e-9:
            raise ValueError("Explicit unit global gravity direction required")
        self._raw_metadata = deepcopy(raw_metadata)
        self._states = {}
        self._tick = 0
        self._active = False

    @property
    def tick(self): return self._tick

    @property
    def raw_metadata(self): return deepcopy(self._raw_metadata)

    def _validate_goals(self, goals):
        if set(goals) != set(self.parameters) or any(not isinstance(goal, Goal) for goal in goals.values()):
            raise ValueError("Exact complete rigid goal set required")

    def reset(self, goals):
        self._validate_goals(goals)
        seeded = {key: State(goals[key].tip(parameters), ZERO) for key, parameters in self.parameters.items()}
        self._states = seeded
        self._tick = 0
        self._active = True

    def snapshot(self):
        return (self._active, self._tick, tuple((key, self._states[key]) for key in sorted(self._states)))

    def step(self, next_tick, goals, external_accelerations=None):
        if not self._active or type(next_tick) is not int or next_tick != self._tick + 1:
            raise ValueError("Active sequential integer ticks required; reset on discontinuity")
        self._validate_goals(goals)
        forces = external_accelerations or {}
        if not isinstance(forces, dict) or not set(forces).issubset(self.parameters):
            raise ValueError("External acceleration identifies an unknown rule")
        checked = {key: vector(forces.get(key, ZERO)) for key in self.parameters}
        if any(length(value) > 1e6 for value in checked.values()):
            raise ValueError("External acceleration outside prototype bound")
        results = {key: solve_one(self.parameters[key], goals[key], self._states[key], checked[key], self.gravity_down) for key in sorted(self.parameters)}
        self._states = {key: result.state for key, result in results.items()}
        self._tick = next_tick
        return results

    def stop(self):
        self._states = {}
        self._active = False
        self._tick = 0
