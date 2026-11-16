"""Independent unchanged-goal boundary oracle for the experimental spring math."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import types

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.absolute()
    assert source.is_relative_to(ROOT / 'experiments')
    assert output.parent == Path(__file__).resolve().parent and not output.exists()
    raw = source.read_bytes()
    name = 'root_frozen_source_math'
    module = types.ModuleType(name)
    sys.modules[name] = module
    exec(compile(raw, str(source), 'exec'), module.__dict__)
    errors = []
    for index in range(1, 1001):
        angle = index * .0031
        c, s = math.cos(angle), math.sin(angle)
        goal = module.Goal(basis=((c, 0., -s), (0., 1., 0.), (s, 0., c)))
        parameters = module.Parameters(tip_mass=0., angle_limit=0.)
        actor = module.Actor({'hair': parameters})
        actor.reset({'hair': goal})
        try:
            result = actor.step(1, {'hair': goal})['hair']
            displacement = module.length(module.subtract(result.state.tip, goal.tip(parameters)))
            if displacement > 1e-10:
                errors.append({'case': index, 'error': 'Unexpected displacement at zero force'})
        except Exception as error:
            errors.append({'case': index, 'type': type(error).__name__, 'error': str(error)})
    assert source.read_bytes() == raw
    proof = {'format': 'has_root_source_math_zero_angle_boundary_1',
             'source_sha256': hashlib.sha256(raw).hexdigest(),
             'cases': 1000, 'failures': len(errors), 'first_failures': errors[:12],
             'expected': 'Zero acceleration at an unchanged goal with zero cone should preserve the seeded rest position',
             'apps_run': False}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
