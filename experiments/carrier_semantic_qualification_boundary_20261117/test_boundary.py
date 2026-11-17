"""Synthetic admission-boundary witnesses; never generate a GLB or read a native asset."""
import copy
import hashlib
from pathlib import Path
import struct
import sys
import unittest

SOURCE = Path(__file__).resolve().parent.parent / 'carrier_semantic_preservation_20261117'
PINS = {'INDEX.json': 'edab37a065d3c29a316b7a1c1cab3a4263f5d4e716f97fa4192f541b391ea4fd',
        'semantic_compare.py': 'c7e1e9d323bb7f35fffa38731a67b0099f173167bcb65d857a7cd6165698ff00',
        'test_semantic_compare.py': '7bd47a8cc6fd03c38f8ce3092326a7205b61c39e06a6b88619576b9543354266'}
for name, digest in PINS.items():
    assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == digest, name
sys.path.insert(0, str(SOURCE))
from semantic_compare import Refusal, compare_non_normal
from test_semantic_compare import fixture, carrier_and_relayout, change_component


class QualificationBoundaryTests(unittest.TestCase):
    def admitted_preservation(self, before):
        after = carrier_and_relayout(*before)
        report = compare_non_normal(*before, *after)
        self.assertTrue(report['passed'])
        self.assertFalse(report['normal_fidelity_qualified'])
        self.assertFalse(report['native_carrier_correspondence_qualified'])
        return after

    def test_valid_synthetic_reference_preservation(self):
        self.admitted_preservation(fixture())

    def test_out_of_skin_domain_joint_is_preserved_but_not_validated(self):
        before = change_component(*fixture(), 'JOINTS_0', b'\xff')
        self.assertEqual(len(before[0]['skins'][0]['joints']), 1)
        self.admitted_preservation(before)

    def test_duplicate_joint_list_is_preserved_but_not_validated(self):
        doc, blob = fixture(); doc = copy.deepcopy(doc); binary = bytearray(blob)
        skin = doc['skins'][0]; skin['joints'] = [1, 1]
        accessor = doc['accessors'][skin['inverseBindMatrices']]
        view = doc['bufferViews'][accessor['bufferView']]
        old = blob[view['byteOffset']:view['byteOffset'] + view['byteLength']]
        binary.extend(b'\0' * (-len(binary) % 4)); view.update(byteOffset=len(binary), byteLength=128)
        binary.extend(old + old); accessor['count'] = 2; doc['buffers'][0]['byteLength'] = len(binary)
        self.admitted_preservation((doc, bytes(binary)))

    def test_VEC3_rotation_output_is_preserved_but_not_validated(self):
        doc, blob = fixture(); doc['animations'][0]['channels'][0]['target']['path'] = 'rotation'
        output = doc['animations'][0]['samplers'][0]['output']
        self.assertEqual(doc['accessors'][output]['type'], 'VEC3')
        self.admitted_preservation((doc, blob))

    def test_node_cycle_is_preserved_but_not_validated(self):
        doc, blob = fixture(); doc['nodes'][1]['children'] = [0]
        self.admitted_preservation((doc, blob))

    def test_changed_joint_component_still_refuses(self):
        before = fixture(); after = carrier_and_relayout(*before)
        after = change_component(*after, 'JOINTS_0', b'\xff')
        with self.assertRaises(Refusal): compare_non_normal(*before, *after)

    def test_changed_position_component_still_refuses(self):
        before = fixture(); after = carrier_and_relayout(*before)
        after = change_component(*after, 'POSITION', struct.pack('<f', .5))
        with self.assertRaises(Refusal): compare_non_normal(*before, *after)


if __name__ == '__main__': unittest.main(verbosity=2)
