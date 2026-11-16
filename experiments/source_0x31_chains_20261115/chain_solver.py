"""Unintegrated HAS parent-first orchestration; no native-client parity claim.

Only mathematical scalar64 frames enter here. Actual float32 Skeleton inputs
need the separately bounded adapter. The pinned single-rule solver is reused
without changing its semantics, clock, constraints, or original failure history.
"""
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from pathlib import Path
import hashlib
import importlib.util
import math
import sys

REFERENCE = Path(__file__).resolve().parents[1] / "source_0x31_candidate_20261115/candidate.py"
REFERENCE_SHA = "dd472f2b4de64adebc83a03c2e812ac2e14805c752b220c26c53dd58bf99519c"
if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != REFERENCE_SHA:
    raise ValueError("Retained single-rule candidate changed")
_spec = importlib.util.spec_from_file_location("has_chain_pinned_math", REFERENCE)
math0 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = math0
_spec.loader.exec_module(math0)


def mv(columns, value):
    return tuple(sum(columns[j][i] * value[j] for j in range(3)) for i in range(3))


def mm(a, b): return tuple(mv(a, column) for column in b)
def transpose(a): return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class Frame:
    origin: tuple = math0.ZERO
    basis: tuple = math0.IDENTITY
    scale: float = 1.

    def __post_init__(self):
        validated = math0.Goal(self.origin, self.basis)
        object.__setattr__(self, "origin", validated.base)
        object.__setattr__(self, "basis", validated.basis)
        if isinstance(self.scale, bool) or not isinstance(self.scale, (int, float)) or not math.isfinite(self.scale) or not 1e-8 <= self.scale <= 1e6:
            raise ValueError("Finite positive bounded uniform scale required")

    def compose(self, child):
        if not isinstance(child, Frame): raise ValueError("Explicit Frame required")
        return Frame(math0.add(self.origin, math0.multiply(mv(self.basis, child.origin), self.scale)),
                     mm(self.basis, child.basis), self.scale * child.scale)


@dataclass(frozen=True)
class Bone:
    parent: str | None
    base: Frame = Frame()


@dataclass(frozen=True)
class TickResult:
    # Mapping proxies with immutable nested dataclasses/tuples prevent aliasing.
    worlds: object
    goals: object
    outputs: object
    delta_bases: object


def parent_order(bones):
    if not bones or len(bones) > 1024 or any(not isinstance(k, str) or not k or not isinstance(v, Bone) or not isinstance(v.base, Frame) for k, v in bones.items()):
        raise ValueError("Explicit named bounded bone hierarchy required")
    if any(v.parent is not None and (not isinstance(v.parent, str) or v.parent not in bones) for v in bones.values()):
        raise ValueError("Missing/invalid actual parent; use None only for Skeleton roots")
    pending = set(bones)
    ordered = []
    while pending:
        ready = sorted(k for k in pending if bones[k].parent is None or bones[k].parent in ordered)
        if not ready: raise ValueError("Cyclic actual parent graph")
        ordered.extend(ready)
        pending.difference_update(ready)
    return tuple(ordered)


class ChainActor:
    """A complete Skeleton baseline is caller-owned, sampled once per tick.

    Every authored absolute parent-local pose is recomposed under the current
    solved parent. Rules replace orientation only; child translation and scale
    remain authored. Unsimulated intermediate bones are recomposed too. States
    remain independent per rule and are committed only after every rule succeeds.
    Root prefix is Skeleton.global_transform, not an assumed Model root.
    """
    def __init__(self, bones, native_parameters, source_scale=.01905,
                 gravity_down=(0., -1., 0.), raw_metadata=None):
        self.order = parent_order(bones)
        if not native_parameters or not set(native_parameters).issubset(bones) or any(not isinstance(p, math0.Parameters) for p in native_parameters.values()):
            raise ValueError("Explicit supported rule owners required")
        if isinstance(source_scale, bool) or not isinstance(source_scale, (int, float)) or not math.isfinite(source_scale) or source_scale <= 0:
            raise ValueError("Explicit positive native-to-HAS source scale required")
        self.bones = MappingProxyType(dict(bones))
        self.parameters = MappingProxyType(dict(native_parameters))
        self.source_scale = source_scale
        self.gravity_down = math0.vector(gravity_down)
        if abs(math0.length(self.gravity_down) - 1) > 1e-9: raise ValueError("Unit world gravity direction required")
        self._metadata = deepcopy(raw_metadata)
        self._states = {}
        self._world_sizes = {}
        self._tick = 0
        self._active = False

    def _validate_baseline(self, locals_by_id, prefix):
        if not isinstance(prefix, Frame) or set(locals_by_id) != set(self.bones) or any(not isinstance(f, Frame) for f in locals_by_id.values()):
            raise ValueError("Exact complete fresh authored local baseline and Skeleton prefix required")
        # Model.apply retains base scale. A user scale edit requires reset/replay.
        if any(locals_by_id[k].scale != self.bones[k].base.scale for k in self.order):
            raise ValueError("Authored local scale differs from Model base contract")

    def baseline_worlds(self, locals_by_id, prefix):
        self._validate_baseline(locals_by_id, prefix)
        worlds = {}
        for key in self.order:
            parent = self.bones[key].parent
            worlds[key] = (prefix if parent is None else worlds[parent]).compose(locals_by_id[key])
        return worlds

    def reset(self, locals_by_id, prefix=Frame()):
        worlds = self.baseline_worlds(locals_by_id, prefix)
        parameters = {k:p.translated_size(self.source_scale * worlds[k].scale) for k,p in self.parameters.items()}
        seeded = {k:math0.State(math0.Goal(worlds[k].origin, worlds[k].basis).tip(parameters[k]), math0.ZERO) for k in parameters}
        self._states = seeded
        self._world_sizes = {k:worlds[k].scale for k in parameters}
        self._tick = 0
        self._active = True

    def snapshot(self):
        return (self._active, self._tick, tuple((k, self._states[k], self._world_sizes[k]) for k in sorted(self._states)))

    def metadata_copy(self): return deepcopy(self._metadata)

    def step(self, next_tick, locals_by_id, prefix=Frame(), world_accelerations=None):
        if not self._active or type(next_tick) is not int or next_tick != self._tick + 1:
            raise ValueError("Sequential120Hz integer ticks required; reset/replay on discontinuity")
        self._validate_baseline(locals_by_id, prefix)
        forces = {} if world_accelerations is None else world_accelerations
        if not isinstance(forces, dict) or not set(forces).issubset(self.parameters): raise ValueError("Unknown rule acceleration")
        checked = {k:math0.vector(forces.get(k, math0.ZERO)) for k in self.parameters}
        if any(math0.length(v) > 1e6 for v in checked.values()): raise ValueError("Unbounded external acceleration")
        worlds, goals, outputs, deltas = {}, {}, {}, {}
        for key in self.order:
            parent_id = self.bones[key].parent
            parent = prefix if parent_id is None else worlds[parent_id]
            goal = parent.compose(locals_by_id[key])
            if key not in self.parameters:
                worlds[key] = goal
                continue
            if goal.scale != self._world_sizes[key]: raise ValueError("Scale changed; explicit reset required")
            p = self.parameters[key].translated_size(self.source_scale * goal.scale)
            target = math0.Goal(goal.origin, goal.basis)
            solved = math0.solve_one(p, target, self._states[key], checked[key], self.gravity_down)
            worlds[key] = Frame(goal.origin, solved.basis, goal.scale)
            goals[key] = goal
            outputs[key] = solved
            # Model rotation=baseQ*deltaQ; Skeleton world=parentWorld*localPose.
            deltas[key] = mm(transpose(self.bones[key].base.basis), mm(transpose(parent.basis), solved.basis))
            math0.Goal(math0.ZERO, deltas[key])  # reject before actor-wide commit
        self._states = {k:result.state for k,result in outputs.items()}
        self._tick = next_tick
        return TickResult(*(MappingProxyType(v) for v in (worlds, goals, outputs, deltas)))

    def stop(self):
        self._active = False
        self._states = {}
        self._world_sizes = {}
        self._tick = 0
