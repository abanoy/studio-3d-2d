"""Isolated executable contract prototype, not installed HAS import code.

No file/model IO, geometry/classification inference, renderer, or subprocesses.
Callers must authenticate an assessment and complete all existing project checks.
"""
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import re

FORMAT = 'studio_import_basis_1'
CAPABILITY_SCHEMA = 9
TARGET = Decimal('1.8288')
SOURCE_UNIT = Fraction(381, 20000)  # Source conversion remains .01905 metres/unit.
# Prototype guard only, chosen to match the current artist-scale numeric range.
# It is not an instruction to change the artist scale or a general import limit.
MIN_FACTOR, MAX_FACTOR = Decimal('0.001'), Decimal('10000')
DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
BASIS_KEYS = frozenset(('format', 'purpose', 'source_sha256', 'measured_from_sha256',
    'factor', 'target_metres', 'measured_converted_height', 'measurement_algorithm',
    'reference_pose', 'classification', 'decision'))


class BasisError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BasisError(message)


def decimal_text(value):
    require(type(value) is str and len(value) <= 96 and DECIMAL.fullmatch(value) is not None,
            'Canonical bounded positive decimal text required')
    result = Decimal(value)
    require(result > 0, 'Positive decimal required')
    return result


def canonical(value):
    raw = format(value, 'f')
    return raw.rstrip('0').rstrip('.') if '.' in raw else raw


def factor_for(height_text):
    height = decimal_text(height_text)
    with localcontext() as context:
        context.prec = 50
        factor = TARGET / height
    require(MIN_FACTOR <= factor <= MAX_FACTOR, 'Basis factor outside prototype supported range')
    return canonical(factor)


def make_basis(source_sha256, measured_height, decision='automatic_qualified'):
    require(type(source_sha256) is str and SHA.fullmatch(source_sha256) is not None,
            'Exact converted-source SHA required')
    require(decision in ('automatic_qualified', 'explicit_complete_human_override'),
            'Unknown complete-human decision')
    return dict(format=FORMAT, purpose='standard_complete_human_six_feet',
        source_sha256=source_sha256, measured_from_sha256=source_sha256,
        factor=factor_for(measured_height), target_metres='1.8288',
        measured_converted_height=measured_height,
        measurement_algorithm='neutral_complete_human_height_1',
        reference_pose='neutral_default', classification='verified_complete_human', decision=decision)


def factor(model, *, capability=False):
    """Strict basis-only validation; absence is identity, including old diagnostics."""
    require(type(model) is dict, 'Model dictionary required')
    if 'asset_basis' not in model:
        return Decimal(1)
    require(capability, 'Active import basis requires project schema9 capability')
    require(model.get('kind', 'model') == 'model', 'Import basis is only for complete character models')
    record = model['asset_basis']
    require(type(record) is dict and frozenset(record) == BASIS_KEYS, 'Unknown import-basis fields')
    require(record['format'] == FORMAT and record['purpose'] == 'standard_complete_human_six_feet',
            'Unsupported import basis')
    require(record['source_sha256'] == model.get('sha256') and
            record['measured_from_sha256'] == record['source_sha256'] and
            type(record['source_sha256']) is str and SHA.fullmatch(record['source_sha256']) is not None,
            'Basis source changed; authenticated derivative support is not implemented')
    require(record['target_metres'] == '1.8288' and
            record['measurement_algorithm'] == 'neutral_complete_human_height_1' and
            record['reference_pose'] == 'neutral_default' and
            record['classification'] == 'verified_complete_human' and
            record['decision'] in ('automatic_qualified', 'explicit_complete_human_override'),
            'Unsupported basis measurement facts')
    parsed = decimal_text(record['factor'])
    require(record['factor'] == factor_for(record['measured_converted_height']),
            'Stored factor differs from the deterministic reviewed height ratio')
    return parsed


def prepare_fresh_import(model, assessment, *, fresh_raw, intent='standard_complete_human'):
    """Build a new dictionary only; never commits/normalizes saved HAS or partials.

    Assessment is an authenticated caller input, not a classifier implemented here.
    A source SHA alone does not establish that an assessment is factually correct.
    """
    require(type(model) is dict and type(assessment) is dict, 'Model and assessment required')
    require(intent in ('standard_complete_human', 'preserve_original', 'complete_human_override'),
            'Unknown per-model import intent')
    result = deepcopy(model)
    if 'asset_basis' in model:
        factor(model, capability=True)
        return result, 'already_standardized'
    if not fresh_raw:
        return result, 'saved_or_legacy_identity'
    if model.get('kind', 'model') != 'model':
        return result, 'non_character_identity'
    if intent == 'preserve_original':
        return result, 'owner_preserved_original'
    classification = assessment.get('classification')
    if classification in ('partial', 'prop', 'tool', 'map', 'multiple_figures'):
        return result, 'ineligible_identity'
    accepted = classification == 'verified_complete_human' or (
        classification == 'reviewed_complete_human' and intent == 'complete_human_override')
    if not accepted:
        return result, 'uncertain_identity'
    require(assessment.get('source_sha256') == model.get('sha256'), 'Stale height assessment')
    require(assessment.get('neutral_reference') is True and assessment.get('height_reviewed') is True and
            assessment.get('positive_uniform_root') is True,
            'A complete neutral reviewed measurement is required')
    require(type(model.get('scale')) in (int, float) and model['scale'] == 1 and
            not model.get('pose_keys'), 'Fresh intrinsic basis must not rewrite authored scale or keys')
    result['asset_basis'] = make_basis(model['sha256'], assessment.get('height_metres'),
        'explicit_complete_human_override' if intent == 'complete_human_override' else 'automatic_qualified')
    factor(result, capability=True)
    return result, 'standardized_complete_human'


def _whole(value, minimum, maximum):
    return type(value) in (int, float) and minimum <= value <= maximum and int(value) == value


def _content_version(document):
    """Validate wrapper ordering only, not the rest of a legacy project schema."""
    require(type(document) is dict, 'Project dictionary required')
    version = document.get('schema_version')
    require(_whole(version, 3, 9), 'Unsupported project schema')
    wrapped = version == 9
    if wrapped:
        require(document.get('import_basis_capability') == FORMAT and
                _whole(document.get('basis_content_schema_version'), 3, 8), 'Invalid basis capability wrapper')
        version = document['basis_content_schema_version']
    else:
        require('basis_content_schema_version' not in document and 'import_basis_capability' not in document,
                'Basis wrapper marker requires schema9')
    if version == 8:
        require(_whole(document.get('timing_content_schema_version'), 3, 7), 'Invalid timing wrapper')
        version = document['timing_content_schema_version']
    else:
        require('timing_content_schema_version' not in document, 'Timing marker requires timing wrapper')
    if version == 7:
        require(_whole(document.get('content_schema_version'), 3, 6) and
                type(document.get('reference_sheet')) is dict, 'Invalid reference wrapper')
        version = document['content_schema_version']
    else:
        require('content_schema_version' not in document and 'reference_sheet' not in document,
                'Reference fields require reference wrapper')
    return int(version), wrapped


def _slots(document, content_version):
    if content_version == 3:
        require('world' not in document, 'Schema3 cannot contain a world')
        scene = document.get('scene', {})
        require(type(scene) is dict and 'asset_basis' not in scene, 'A map cannot carry a character basis')
        model = document.get('model', {})
        require(type(model) is dict, 'Model slot must be a dictionary')
        return [model] if model else []
    world = document.get('world')
    require(type(world) is dict and type(world.get('objects')) is list and len(world['objects']) <= 64,
            'Bounded world required')
    require('model' not in document and 'scene' not in document, 'Obsolete model/map slots in world project')
    return world['objects']


def existing_child_schema(document):
    """Match current Extended.child_schema after peeling ONLY the new wrapper.

    A reference wrapper is not newly authorized inside a sequence. Existing
    timing wrappers can contain4/5, exactly as in the current child gate.
    """
    _content_version(document)
    version = document.get('basis_content_schema_version') if document['schema_version'] == 9 else document['schema_version']
    if version == 8:
        version = document['timing_content_schema_version']
    return int(version)


def _children(document, content_version, child):
    graph = document.get('sequence_graph')
    if content_version != 6:
        require(graph is None, 'Sequence graph requires schema6 content')
        return []
    require(not child, 'Nested child sequence graphs remain unsupported')
    require(type(graph) is dict and type(graph.get('assets')) is list and 1 <= len(graph['assets']) <= 4,
            'Bounded existing sequence graph required')
    result = []
    for asset in graph['assets']:
        require(type(asset) is dict and type(asset.get('scene')) is dict, 'Invalid sequence scene')
        result.append(asset['scene'])
    return result


def encode_capability(document, *, _child=False):
    """Writer's capability-only pass, after the existing full legacy validation.

    Preserves legacy/timing/reference data, wraps each active child separately,
    and wraps the root when any child is active. No resource gate is replaced.
    """
    content, wrapped = _content_version(document)
    if wrapped:
        inspect_capability(document, _child=_child)
        return deepcopy(document)
    require(not _child or existing_child_schema(document) in (4, 5), 'Child scenes must retain existing world4/5 schema admission')
    result = deepcopy(document)
    own = False
    for model in _slots(result, content):
        factor(model, capability=True)
        own |= 'asset_basis' in model
    nested = False
    for scene in _children(result, content, _child):
        encoded = encode_capability(scene, _child=True)
        scene.clear()
        scene.update(encoded)
        nested |= encoded['schema_version'] == 9
    if own or nested:
        result['basis_content_schema_version'] = result['schema_version']
        result['schema_version'] = 9
        result['import_basis_capability'] = FORMAT
    inspect_capability(result, _child=_child)
    return result


def inspect_capability(document, *, _child=False):
    """Reader's capability gate. Permission is scene-local, never inherited."""
    content, wrapped = _content_version(document)
    require(not _child or existing_child_schema(document) in (4, 5), 'Child scenes must retain existing world4/5 schema admission')
    own = False
    count = 0
    for model in _slots(document, content):
        factor(model, capability=wrapped)
        own |= 'asset_basis' in model
        count += 1
    nested = False
    for scene in _children(document, content, _child):
        child = inspect_capability(scene, _child=True)
        nested |= child['basis_required']
        count += child['object_count']
    require(count <= 64, 'Existing shared64-object budget exceeded')
    active = own or nested
    require(wrapped == active, 'Missing or redundant schema9 capability')
    return {'basis_required': active, 'content_schema': content, 'object_count': count,
            'own_scene_permission': wrapped}


def _legacy_validation_view(document):
    # Only called after the complete scene-local capability gate succeeded.
    # This transient copy is for old metadata/resource validators, never output.
    out = deepcopy(document)
    content, wrapped = _content_version(out)
    if wrapped:
        out['schema_version'] = out.pop('basis_content_schema_version')
        out.pop('import_basis_capability')
    for scene in _children(out, content, False):
        view = _legacy_validation_view(scene)
        scene.clear()
        scene.update(view)
    return out


def members_with_capability(document, legacy_members):
    """First safe Python container entrypoint: basis gate plus old resource gate.

    `legacy_members` must be the unchanged old implementation, including its
    existing recursive calls. Installing a facade requires renaming that old
    function AND its four recursive members calls together; otherwise the
    facade would accidentally recheck a transient unwrapped scene. The active
    original manifest is retained by the caller and must never be replaced by
    this transient validation view.
    """
    inspect_capability(document)
    return legacy_members(_legacy_validation_view(document))


def identity_matrix():
    return tuple(tuple(Fraction(int(i == j)) for j in range(4)) for i in range(4))


def multiply(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)) for i in range(4))


@dataclass(frozen=True)
class ImportRoot:
    """Synthetic exact matrix prototype of C*B0; always retains immutable raw B0."""
    raw_root: tuple
    basis_factor: Fraction

    @classmethod
    def configured(cls, raw_root, model, *, capability=False):
        require(type(raw_root) is tuple and len(raw_root) == 4 and
                all(type(row) is tuple and len(row) == 4 for row in raw_root), 'Raw4x4 root required')
        require(all(type(v) in (int, Fraction) for row in raw_root for v in row), 'Exact synthetic matrix values required')
        require(raw_root[3] == (0, 0, 0, 1), 'Affine root required')
        return cls(raw_root, Fraction(factor(model, capability=capability)))

    def effective_base(self):
        c = tuple(tuple(self.basis_factor if i == j and i < 3 else Fraction(int(i == j))
                        for j in range(4)) for i in range(4))
        return multiply(c, self.raw_root)

    def evaluate(self, artist_transform):
        return multiply(artist_transform, self.effective_base())
