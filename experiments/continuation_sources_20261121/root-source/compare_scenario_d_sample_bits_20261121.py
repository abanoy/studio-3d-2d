"""Read-only independent standard-library comparison; no Godot/reader launch."""
from pathlib import Path
import hashlib
import json
import math
import struct

ROOT = Path(__file__).resolve().parent
CASE = ROOT / 'import-off-followup-scoped-1795256798459581600/scenario-d-artifacts'
PINS = {
    'expected.json': (446644, '6a5aeae9746ac6f04851593183f6ca2541aca330fe2020747db13e2d07a2eca2'),
    'actual-stamps-diagnostic.json': (217545, '0dc5583624e239a6c1b1bc3d069ad5056a345aaf072ee221000d96aa49bb3150'),
}


def identity(path):
    value = path.stat()
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def main():
    original = {}
    documents = {}
    for name, pin in PINS.items():
        path = CASE / name
        original[name] = identity(path)
        raw = path.read_bytes()
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == pin
        assert identity(path) == original[name]
        documents[name] = json.loads(raw)
    expected = documents['expected.json']['samples']
    actual = documents['actual-stamps-diagnostic.json']
    assert set(expected) == set(actual) == {str(i) for i in range(49)}
    counts = {'frames': 49, 'numeric_values': 0, 'float64_bit_differences': 0,
              'float32_bit_differences': 0, 'structure_differences': 0,
              'non_numeric_value_differences': 0, 'raw_text_differences': 0}
    differences = []

    def walk(a, b, path):
        if type(a) is dict:
            if type(b) is not dict or set(a) != set(b):
                counts['structure_differences'] += 1
                return
            for index, name in enumerate(sorted(a)):
                label = f'actor#{index}' if len(path) == 1 else name
                walk(a[name], b[name], path + [label])
        elif type(a) is list:
            if type(b) is not list or len(a) != len(b):
                counts['structure_differences'] += 1
                return
            for index, (left, right) in enumerate(zip(a, b)):
                walk(left, right, path + [str(index)])
        elif type(a) in (int, float) and type(b) in (int, float):
            assert math.isfinite(a) and math.isfinite(b)
            counts['numeric_values'] += 1
            left64, right64 = struct.pack('<d', a), struct.pack('<d', b)
            left32, right32 = struct.pack('<f', a), struct.pack('<f', b)
            counts['float32_bit_differences'] += left32 != right32
            if left64 != right64:
                counts['float64_bit_differences'] += 1
                differences.append({'path': '/'.join(path), 'expected': a, 'actual': b,
                                    'absolute_delta': abs(a-b), 'expected_f64_le': left64.hex(),
                                    'actual_f64_le': right64.hex(), 'expected_f32_le': left32.hex(),
                                    'actual_f32_le': right32.hex()})
        else:
            counts['non_numeric_value_differences'] += type(a) is not type(b) or a != b

    for frame in range(49):
        key = str(frame)
        assert type(expected[key]) is type(actual[key]) is str
        counts['raw_text_differences'] += expected[key] != actual[key]
        walk(json.loads(expected[key]), json.loads(actual[key]), [f'frame{frame}'])
    for name in PINS:
        assert identity(CASE / name) == original[name]
        raw = (CASE / name).read_bytes()
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == PINS[name]
    assert counts == {'frames': 49, 'numeric_values': 7399, 'float64_bit_differences': 1,
                      'float32_bit_differences': 0, 'structure_differences': 0,
                      'non_numeric_value_differences': 0, 'raw_text_differences': 1}
    print(json.dumps({'format': 'has_independent_scenario_d_bits_child_1', 'status': 'PASS',
                      'counts': counts, 'differences': differences, 'inputs_unchanged': True,
                      'reader_or_Godot_execution': False, 'oracle_or_Main_changed': False}, indent=2))


if __name__ == '__main__':
    main()
