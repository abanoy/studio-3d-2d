"""Exclusive source-pin + synthetic CPU audit; no native input or subprocess."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCEIO = ROOT / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
SOURCE_PINS = {
    'library/models/mdl/structs/header.py': '03fe4f685c3818785c9b5ff81356f91aa9ab8160d1a17ca27e57520a1c37f57f',
    'library/models/mdl/structs/bodygroup.py': '34d41c35681550fe4512c0541bcb859c076a960d04054efb633c098ff70c17b8',
    'library/models/mdl/structs/model.py': 'd11d7e0235e2607f8d4ca2e5e32ca482969035277f274b57f713df8e8ba0c176',
    'library/models/mdl/structs/mesh.py': 'ea5c9d478b40924e8610c3d4699b894f6b4f56a375b0594ebfb581d80100ef71',
    'library/models/mdl/structs/bone.py': 'a61a3e0378e7b2d2d070f2b9ef138b78516db4a9830144cd6a6d907295b7d085',
    'library/models/vvd/__init__.py': '2dc91e450ed1b32835c5b133360e8f56d923785d20aecce2c39a312b754a17ed',
    'library/models/vtx/v7/vtx.py': 'b1faa3708c50ded62c912bb76b20e8773686f5bef56bf4740229cef0d98fad5c',
    'library/models/vtx/v7/structs/bodypart.py': '1c5e4b1a5028ef34c8aed9e5c82802253968d9eee1e702133631534f232cd1b3',
    'library/models/vtx/v7/structs/model.py': '2d2675645364eb35ae5ea249e1c15a6166edd30700ee59249365eb0ff46d8d5b',
    'library/models/vtx/v7/structs/lod.py': '189d2d4373472dae06c591db7cc445bd7d62e2abab1c4418dc96f455bb7a4ec6',
    'library/models/vtx/v7/structs/mesh.py': 'efc8ed89687e30cdd2e27f54ca6cf0ac3869e0517df0d6df6484cdb245fc3ba7',
    'library/models/vtx/v7/structs/strip_group.py': '018626db3f6bc6a1f436cdd0bb4e9f67a07e42f244b8ccad354a99b01a4f29c2',
    'library/models/vtx/v7/structs/strip.py': '51fb7903c7b9e25bde4612757d5e421675c14b49816d6fb09974e9d5eb6f2d8d',
    'library/models/vtx/v7/structs/material_replacement_list.py': '8aceb79ca4e820c7a4f42a5a0787102aaba4d8d45a7d2b8d2e15c37ca9177a1d',
    'library/utils/file_utils.py': '6d91d0eae0ea912aff31dc210f24665bf4303f71c00ebc3b4245aaf775185ba0',
    'library/models/vtx/v6/structs/header.py': '90ed3a9cc0d187a579857d1a729d6e31941cae70c675e73766ef9953fb43d03c',
    'blender_bindings/models/mdl49/import_mdl.py': '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b',
    'blender_bindings/models/mdl44/import_mdl.py': '080b91589e0fec462e3eea4b55793aec41399ff95f6d9f2d561d5cda9dddada8',
    'blender_bindings/models/common.py': '2522f2a451f082edcfcf66c3b445782716e24feb45f8b43d5d6e459f6408f750',
    'blender_bindings/utils/fast_mesh.py': 'ece5c47ac13eb5885bdc7c5b415784a6c7ea3ecc76d13c620bb561ca9c30058a',
}
PRIOR_PINS = {
    'experiments/native_normal_carrier_probe_20261117/exact_point_join.py': 'c3a5ac1acc6b6a2988020d924313f27fedaa371281bfeae5f6871a545d54d85d',
    'experiments/native_normal_carrier_strategy_20261117/vvd_normals.py': 'f3a959cc8dff0bd03528b20886984857b16a21944d2f5ef627cf4c4c05ebcdfb',
    'experiments/native_normal_carrier_strategy_20261117/normal_identity_carrier.py': '37be746c21274e9844a532698078423a0b4f156dcb546135d18b0217daf0fb08',
    'tools/blender_source_bridge.py': 'c794df555f7872e11d4c341b0ffed2507f371f892b67b715e185105d40026dea',
    'experiments/normal_setter_actual_packet_20261117/ACTUAL_RESULT.json': '344f89738ae5856b088c85495bcbb222e888ca5db401613dd67befcaee50725e',
    'experiments/normal_boundary_probe_sentinel_20261116/capture_blender_normals.py': '07c5d24538b11da7d8f4464b6a1e48dd3bbd6f15525c60c7e5cc4b9619e83576',
}


def identity(path):
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check_pins():
    result = {}
    for base, pins, prefix in ((SOURCEIO, SOURCE_PINS, 'SourceIO/'), (ROOT, PRIOR_PINS, 'ROOT/')):
        for relative, expected in pins.items():
            row = identity(base / relative)
            assert row['sha256'] == expected, relative
            result[prefix + relative] = row
    return result


def write_new(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    expected_names = {'native_point_expectation.py', 'test_native_point_expectation.py', 'audit_cpu.py',
                      'README.md', 'SOURCE_DERIVATION.json', 'PEER_REVIEW.md'}
    assert {path.name for path in HERE.iterdir()} == expected_names, 'Only fresh source packet may be sealed'
    before = check_pins()
    source_before = {name: identity(HERE / name) for name in sorted(expected_names)}
    captured = io.StringIO()
    with redirect_stdout(captured), redirect_stderr(captured):
        suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_native_point_expectation.py')
        result = unittest.TextTestRunner(stream=captured, verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun == 14, captured.getvalue()
    assert check_pins() == before
    assert {name: identity(HERE / name) for name in sorted(expected_names)} == source_before
    report = {'format': 'has_native_point_expectation_source_cpu_audit_1',
              'utc': datetime.now(timezone.utc).isoformat(), 'status': 'SYNTHETIC_CPU_PASS_NATIVE_UNQUALIFIED',
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'generalized_replace_ledger_histories': 8000, 'source_pins_before_after': before,
              'packet_sources_before_after': source_before, 'test_output': captured.getvalue(),
              'original_native_or_private_arrays_read': False, 'native_apps_or_SourceIO_import_executed': False,
              'native_process_or_Git_network_or_installs_executed': False,
              'full_SourceIO574_exporter120_catalogue_or_runtime6_rechecked': False,
              'multi_group_Blender_storage_rule_qualified': False,
              'actual_B_reader_profile_observed': False, 'native_export_or_repair_executed': False,
              'original_2e_5_failure_unchanged': True, 'normal_unit_threshold_2_5e_7_unchanged': True,
              'native_SDK_fidelity_export_repair_adoption_qualified': False}
    write_new('CPU_VALIDATION.json', report)
    members = {path.name: identity(path) for path in sorted(HERE.iterdir()) if path.is_file()}
    write_new('INDEX.json', {'format': 'has_native_point_expectation_source_packet_index_1',
                            'status': 'SOURCE_CPU_CANDIDATE_NATIVE_UNQUALIFIED', 'files': members})
    print(json.dumps({'tests': result.testsRun, 'failures': 0, 'errors': 0,
                      'sourceio_rule_pins': len(SOURCE_PINS), 'unchanged_prior_pins': len(PRIOR_PINS),
                      'index': identity(HERE / 'INDEX.json'), 'native_qualified': False}))


if __name__ == '__main__':
    main()
