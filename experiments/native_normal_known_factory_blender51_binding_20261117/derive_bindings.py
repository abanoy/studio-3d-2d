"""Pure two-literal successor binding over the unchanged Git-only binder."""
import hashlib

PARENT_INDEX = '3917792c091fe776cdd49b7f3e015b5655b104798c8a605e340967e870801235'
PARENT_SOURCE = '972a470717032c32df24194cde81deb7580b6722442114f7c00edcd48a0c01e0'
RUNTIME_INDEX = '82727caa443cc58d623463e195fc6220d08c2d878cb93461eb481c722098b6e0'
RULES = (
    (b"SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_resource_successor_20261117'",
     b"SUCCESSOR = ROOT / 'experiments/native_normal_known_factory_blender51_resource_20261117'"),
    (b"SUCCESSOR_SHA = '1eeca1e85d93c834c52c1208ed68d18aaa2b00bc1b62987cf0b89d5561ab6f90'",
     ("SUCCESSOR_SHA = '" + RUNTIME_INDEX + "'").encode()),
)


def render(raw):
    if hashlib.sha256(raw).hexdigest() != PARENT_SOURCE: raise ValueError('exact Git-only parent binder required')
    result = raw
    for old, new in RULES:
        if result.count(old) != 1: raise ValueError('unique runtime binding required')
        result = result.replace(old, new, 1)
    inverse = result
    for old, new in reversed(RULES):
        if inverse.count(new) != 1: raise ValueError('unique runtime inverse required')
        inverse = inverse.replace(new, old, 1)
    if inverse != raw: raise ValueError('whole binder byte inverse differs')
    compile(result, 'prepare_root.py', 'exec')
    return result
