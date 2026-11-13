# PROPOSAL: append these definitions to tests/native_fixture_plans.py.
# Existing Path/hashlib/json/fixture_output imports and functions stay unchanged.
WIND_REVIEW_PINS = {
    'vrm0': {'source': '3caa50b76d0f481bb7ee66daeb6ebe7485aefb966140321b599ca60d9d464b56',
             'parameters': '0f8f746ca68a821acaf9e502b6895a2f2798d8d1d2bd62569d78deea652fc0ef',
             'raw': 'f7b4573b241b3e91c7c5f58bed342133a4e5f7e0c1125e1cedc49723ace9b288',
             'family': '0.x'},
    'vrm1': {'source': 'a0b095f399e0f7f95c88b91d12e74f8d1816052c1552b9d2dd758ceed8a6b062',
             'parameters': '21f11bfb2c606fd13fa21e2d4cdbe130555918b52f92ff6030598b10ce680372',
             'raw': '14d2b2c751e2d6b7739471b961d71b7b16ca28089c04d9465b9c71a113033ee3',
             'family': '1.0'},
    'backhair': {'source': '4d62236d5c34468ea1f91c43089d6ce3c193be27b8460d53ea8d91d2238ab7b5',
                 'parameters': 'f4e1850d9f4fa9359a72d43f3c945aaf61a1bd726538b025da31c4fa5f8071ba',
                 'raw': '66442ce25e36ca4a8dbccbe0c321278d4d2afbbd5603495d470ad366f869a88b'}
}


def wind_review_native_plans(manifest=None):
    """Resolve exact approved wind inputs; missing/different inputs are failures."""
    import os
    import stat
    from pathlib import PureWindowsPath

    raw_base = Path(os.environ['HYBRID_NATIVE_FIXTURES']).expanduser().absolute() if os.environ.get('HYBRID_NATIVE_FIXTURES') else ROOT / 'output'
    for part in (raw_base, *raw_base.parents):
        if part.exists():
            value = part.lstat()
            if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Wind fixture root refuses links/reparse ancestors')
    base = fixture_output()

    def checked(path):
        path = Path(path).absolute()
        if not path.resolve(strict=True).is_relative_to(base.resolve(strict=True)):
            raise ValueError('Wind fixture path escapes HYBRID_NATIVE_FIXTURES')
        for part in (path, *path.parents):
            value = part.lstat()
            if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Wind fixtures refuse links/reparse paths')
            if part == base:
                break
        if not path.is_file():
            raise ValueError('Wind fixture must be a regular file')
        return path

    def relative(name):
        if not isinstance(name, str) or not name or '..' in Path(name).parts or PureWindowsPath(name).drive or Path(name).is_absolute():
            raise ValueError('Wind fixture manifest paths must be relative descendants')
        return checked(base / name)

    def identity(path):
        info = path.stat()
        return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns}

    path = checked(manifest or base / 'wind-review-inputs.json')
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('Wind fixture manifest exceeds1MiB')
    document = json.loads(path.read_bytes())
    if document.get('format') != 'has_wind_review_inputs_1' or set(document.get('inputs', {})) != set(WIND_REVIEW_PINS):
        raise ValueError('Wind manifest needs exactly VRM0, VRM1 and ribbon-derived Back hair roles')
    result = {}
    for role, pins in WIND_REVIEW_PINS.items():
        row = document['inputs'][role]
        source, parameters = relative(row['source']), relative(row['parameters'])
        source_id, parameters_id = identity(source), identity(parameters)
        if source_id['sha256'] != pins['source'] or parameters_id['sha256'] != pins['parameters']:
            raise ValueError('Wrong checksum-bound wind source/parameter report: ' + role)
        report = json.loads(parameters.read_bytes())
        if report.get('source_sha256') != pins['raw']:
            raise ValueError('Wrong original-native provenance: ' + role)
        if role.startswith('vrm'):
            if report.get('kind') != 'vrm_preparation' or report.get('vrm_version') != pins['family'] or report.get('scale') != 1.0:
                raise ValueError('Wrong prepared VRM family/scale: ' + role)
        elif report.get('source_member') != 'models/player/reimu_hakurei_bikini.mdl' or report.get('sourceio_revision') != 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647':
            raise ValueError('Wrong Reimu player/SourceIO provenance')
        result[role] = {'source': str(source), 'parameters': str(parameters),
                        'source_identity': source_id, 'parameters_identity': parameters_id}
    return {'fixture_root': str(base), 'manifest': str(path),
            'manifest_identity': identity(path), 'inputs': result}
