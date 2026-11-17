"""RAM-only PMX bytes in, private scalar table-count diagnostic out; no input IO."""
from contextlib import contextmanager
from pathlib import Path
import importlib.util
import sys
import types

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_has_passive_count_source_patch', HERE / 'source_patch.py')
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
ORACLE_FOLDER = HERE.parent / 'pmx_physics_independent_oracle_20261117'
TABLES = ('vertex', 'index', 'texture', 'material', 'bone', 'morph', 'display', 'body', 'joint')


def _source():
    # These are exact public source paths, never paths discovered from input bytes.
    with (ORACLE_FOLDER / 'INDEX.json').open('rb') as stream: index = stream.read(1024 * 1024 + 1)
    if len(index) > 1024 * 1024 or P.sha(index) != P.INDEX_SHA256:
        raise ValueError('sealed oracle INDEX differs')
    with (ORACLE_FOLDER / 'oracle.py').open('rb') as stream: raw = stream.read(P.ORACLE_BYTES + 1)
    # instrument_source verifies length, full SHA and exact inverse before execution.
    return P.instrument_source(raw)


@contextmanager
def instrument_module(observer):
    """Fresh original module plus one passive call; caller owns observer lifetime."""
    if not callable(observer): raise TypeError('owned passive observer required')
    patched = _source()
    value = types.ModuleType('_has_passive_pmx_count_' + format(id(patched), 'x'))
    value.__file__ = str(ORACLE_FOLDER / 'oracle.py')
    value.__dict__['_observe_table_count'] = observer
    previous = sys.modules.get(value.__name__)
    sys.modules[value.__name__] = value
    try:
        exec(compile(patched, '<sealed-independent-oracle-plus-passive-count-call>', 'exec'), value.__dict__)
        yield value
    finally:
        if previous is None: sys.modules.pop(value.__name__, None)
        else: sys.modules[value.__name__] = previous


def diagnostic_counts(data):
    """Use exact default limits/traversal, discard witness; returned counts are PRIVATE."""
    observed = []
    def observe(name, count, ceiling, offset):
        # All four values come from the unchanged table() locals before its guard.
        # No callback into the walker, input mutation, discovered paths or raw names.
        if name not in TABLES or len(observed) >= len(TABLES):
            raise RuntimeError('unexpected source-authored table observation')
        observed.append({'table': name, 'count': count, 'ceiling': ceiling,
                         'byte_offset': offset, 'within_count_budget': 0 <= count <= ceiling})
    refusal = None
    with instrument_module(observe) as oracle:
        try:
            witness = oracle.read_oracle(data)
            del witness
        except oracle.Refused as error:
            refusal = {'type': 'Refused', 'label': str(error)}
    return {'format': 'has_passive_pmx_oracle_table_counts_1', 'observed_tables': observed,
            'refusal': refusal, 'traversal_completed': refusal is None,
            'oracle_source_sha256': P.ORACLE_SHA256, 'oracle_INDEX_sha256': P.INDEX_SHA256,
            'original_limits_and_traversal_preserved': True, 'witness_returned': False,
            'candidate_imported_or_run': False, 'count_offset_proves_prefix_correct': False,
            'native_protocol_qualified': False, 'simulation_or_production_adoption': False}
