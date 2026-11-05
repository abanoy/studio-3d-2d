"""Authored geometry/skin preservation and refusal tests; no private models required."""
from pathlib import Path
import copy
import hashlib
import json
import math
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import secondary_helpers as H


def write_glb(path, doc, binary):
    binary += bytes(-len(binary) % 4); doc['buffers'] = [{'byteLength': len(binary)}]
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=True).encode(); encoded += b' ' * (-len(encoded) % 4)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + struct.pack('<II', len(binary), 0x004e4942) + binary)


def fixture(path, quantized=False, eight=False):
    """A rigidly Head-weighted hanging strip and independent body/side patch."""
    doc = {'asset': {'version': '2.0', 'generator': 'HAS original helper fixture', 'extras': {'keep': '日本語'}},
           'scene': 0, 'scenes': [{'name': 'HelperSource', 'nodes': [0]}],
           'nodes': [{'name': 'Rig', 'children': [1, 3]}, {'name': 'Hips', 'children': [2]},
                     {'name': 'Head', 'translation': [0, 2, 0]}, {'name': 'Surface', 'mesh': 0, 'skin': 0}],
           'skins': [{'joints': [1, 2], 'skeleton': 1}], 'meshes': [{'name': 'OriginalSurfaces', 'primitives': []}],
           'materials': [{'name': 'Original textured surface', 'doubleSided': True, 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0, 'roughnessFactor': 1}}],
           'textures': [{'source': 0}], 'bufferViews': [], 'accessors': [], 'buffers': [{'byteLength': 4}]}
    write_glb(path, doc, bytes(4)); g = H.GLB(path)
    # Self-authored 2x2 RGBA texture.
    def chunk(kind, data): return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + bytes([230, 150, 70, 255]) * 2) * 2)) + chunk(b'IEND', b'')
    start = len(g.binary); g.binary.extend(png); g.doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(png)})
    g.doc['images'] = [{'bufferView': 0, 'mimeType': 'image/png', 'name': 'Original pixels'}]
    body = [(-.25, 0, 0), (.25, 0, 0), (-.25, 1.8, 0), (.25, 1.8, 0)]
    strip = [(x, 2 - row * .12, .1) for row in range(10) for x in (.32, .48)]
    strip += [(-.8, .4, .1), (-.3, .4, .1), (-.8, 1.3, .1), (-.3, 1.3, .1)]
    for pi, positions in enumerate((body, strip)):
        # Strided POSITION is read without interpreting the unused fourth float.
        position = g.append([(*p, 123.) for p in positions], 'VEC4'); g.doc['accessors'][position]['type'] = 'VEC3'
        g.doc['accessors'][position]['min'] = [min(p[k] for p in positions) for k in range(3)]; g.doc['accessors'][position]['max'] = [max(p[k] for p in positions) for k in range(3)]
        g.doc['bufferViews'][g.doc['accessors'][position]['bufferView']]['byteStride'] = 16
        js = [[pi, 0, 0, 0] for p in positions]; ws = [[255 if quantized else 1., 0, 0, 0] for p in positions]
        ja = g.append(js, 'VEC4', 5121); wa = g.append(ws, 'VEC4', 5121 if quantized else 5126)
        if quantized: g.doc['accessors'][wa]['normalized'] = True
        attrs = {'POSITION': position, 'NORMAL': g.append([(0, 0, 1)] * len(positions), 'VEC3'),
                 'TEXCOORD_0': g.append([(i % 2, i // 2 % 2) for i in range(len(positions))], 'VEC2'), 'JOINTS_0': ja, 'WEIGHTS_0': wa}
        if eight: attrs.update({'JOINTS_1': g.append([(0, 0, 0, 0)] * len(positions), 'VEC4', 5121), 'WEIGHTS_1': g.append([(0, 0, 0, 0)] * len(positions), 'VEC4')})
        indices = [0, 1, 2, 1, 3, 2] if pi == 0 else [i for row in range(9) for i in (row * 2, row * 2 + 1, row * 2 + 2, row * 2 + 1, row * 2 + 3, row * 2 + 2)] + [20, 21, 22, 21, 23, 22]
        primitive = {'attributes': attrs, 'indices': g.append([(v,) for v in indices], 'SCALAR', 5123), 'material': 0,
                     'targets': [{'POSITION': g.append([(.01, 0, 0)] * len(positions), 'VEC3')}]}
        g.doc['meshes'][0]['primitives'].append(primitive)
    g.doc['meshes'][0]['extras'] = {'targetNames': ['Original morph']}; g.doc['meshes'][0]['weights'] = [0.]
    g.doc['skins'][0]['inverseBindMatrices'] = g.append([H.IDENTITY, H.translation((0, -2, 0))], 'MAT4')
    write_glb(path, g.doc, bytes(g.binary)); return H.GLB(path)


def request(g):
    return {'source_sha256': g.sha, 'reviewed': True, 'node': 3, 'primitive': 1, 'component': 0, 'anchor_node': 2, 'segments': 3}


def mixed_fixture(path):
    g = fixture(path); node = len(g.doc['nodes']); g.doc['nodes'].append({'name': 'Other'}); g.doc['nodes'][1]['children'].append(node)
    g.doc['skins'][0]['joints'].append(node); g.doc['skins'][0]['inverseBindMatrices'] = g.append([H.IDENTITY, H.translation((0, -2, 0)), H.IDENTITY], 'MAT4')
    attrs = g.doc['meshes'][0]['primitives'][1]['attributes']
    attrs['JOINTS_0'] = g.append([(0, 1, 2, 0)] * 24, 'VEC4', 5121); attrs['WEIGHTS_0'] = g.append([(.1, .8, .1, 0)] * 24, 'VEC4')
    write_glb(path, g.doc, bytes(g.binary)); return H.GLB(path)


def two_panel_fixture(path, family=None):
    g = fixture(path); data = g.skin(3, 1); primitive = data[2]
    positions = data[4][:20] + [(x-1.1, y, z) for x, y, z in data[4][:20]]
    primitive['attributes'] = {'POSITION': g.append(positions, 'VEC3'),
        'NORMAL': g.append([(0, 0, 1)]*40, 'VEC3'), 'TEXCOORD_0': g.append([(i%2, i//2%2) for i in range(40)], 'VEC2'),
        'JOINTS_0': g.append([(1, 0, 0, 0)]*40, 'VEC4', 5121), 'WEIGHTS_0': g.append([(1, 0, 0, 0)]*40, 'VEC4')}
    indices = data[5][:54]; primitive['indices'] = g.append([(i,) for i in indices+[i+20 for i in indices]], 'SCALAR', 5123)
    primitive['targets'] = [{'POSITION': g.append([(.01, 0, 0)]*40, 'VEC3')}]
    if family:
        # An existing authored chain under Head, separate from the two still
        # rigidly weighted panels. Its settings/colliders must remain intact.
        g.doc['nodes'][2]['children'] = [4]
        g.doc['nodes'] += [{'name':'Native.A','translation':[0,0,.3],'children':[5]}, {'name':'Native.End','translation':[0,-.2,0]}]
        g.doc['skins'][0]['joints'] += [4,5]
        g.doc['skins'][0]['inverseBindMatrices'] = g.append([H.IDENTITY,H.translation((0,-2,0)),H.translation((0,-2,-.3)),H.translation((0,-1.8,-.3))],'MAT4')
        if family == 'v1':
            g.doc['extensions'] = {'VRMC_springBone': {'specVersion':'1.0', 'springs':[{'name':'Existing native', 'joints':[{'node':4,'stiffness':2.5,'dragForce':.3},{'node':5}], 'center':2, 'colliderGroups':[0]}],
                'colliders':[{'node':2,'shape':{'sphere':{'offset':[0,0,0],'radius':.01}}}], 'colliderGroups':[{'colliders':[0]}]}}
        else:
            g.doc['extensions'] = {'VRM': {'secondaryAnimation': {'boneGroups':[{'comment':'Existing native','bones':[4],'stiffiness':2.5,'dragForce':.3,'center':2,'colliderGroups':[0]}],
                'colliderGroups':[{'node':2,'colliders':[{'offset':{'x':0,'y':0,'z':0},'radius':.01}]}]}}}
    write_glb(path, g.doc, bytes(g.binary)); return H.GLB(path)


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.path = self.root / 'original.glb'; self.g = fixture(self.path)
    def tearDown(self): self.temp.cleanup()
    def build(self, **changes):
        plan = request(self.g); plan.update(changes)
        result = H.build(self.path, self.root / 'derived', plan); return H.GLB(result['glb']), result['report']
    def test_assessment_uses_topology_and_weights_without_source_edits(self):
        before = (self.path.read_bytes(), self.path.stat().st_mtime_ns); result = H.inspect(self.path)
        self.assertEqual((self.path.read_bytes(), self.path.stat().st_mtime_ns), before)
        self.assertEqual(len(result['regions']), 3)
        hair = next(x for x in result['regions'] if x['primitive'] == 1 and x['component'] == 0)
        body = next(x for x in result['regions'] if x['primitive'] == 1 and x['component'] == 1)
        self.assertTrue(hair['suggested']); self.assertFalse(body['suggested']); self.assertEqual(hair['anchor_node'], 2)
        torso = next(x for x in result['regions'] if x['primitive'] == 0)
        self.assertFalse(torso['suggested']); self.assertTrue(torso['existing_joint_near_free_region'])
        self.assertEqual(hair['vertices'], 20); self.assertGreater(hair['length_in_anchor_units'], 1)
        self.assertIn('review', hair['assessment'])
    def test_real_weights_bind_matrices_and_unrelated_attributes_preserved(self):
        before = self.path.read_bytes(); after, report = self.build()
        self.assertEqual(self.path.read_bytes(), before); self.assertTrue(bytes(after.binary).startswith(self.g.binary))
        self.assertEqual(after.doc['materials'], self.g.doc['materials']); self.assertEqual(after.doc['images'], self.g.doc['images'])
        self.assertEqual(after.doc['asset'], self.g.doc['asset']); self.assertEqual(after.doc['accessors'][:len(self.g.doc['accessors'])], self.g.doc['accessors'])
        self.assertEqual(after.doc['nodes'][3]['mesh'], self.g.doc['nodes'][3]['mesh']); self.assertEqual(len(after.doc['meshes']), len(self.g.doc['meshes']))
        old = self.g.skin(3, 1); new = after.skin(3, 1)
        for key in ('POSITION', 'NORMAL', 'TEXCOORD_0'): self.assertEqual(new[2]['attributes'][key], old[2]['attributes'][key])
        self.assertEqual(new[2]['targets'], old[2]['targets']); self.assertEqual(new[4:6], old[4:6]); self.assertEqual(new[6][20:], old[6][20:])
        self.assertEqual(len(new[3]['joints']), 6); self.assertGreater(report['changed_vertices'], 10)
        self.assertEqual(new[6][:2], old[6][:2]); self.assertEqual(report['region']['attachment_vertices'], 2)
        self.assertAlmostEqual(report['points_in_anchor'][0][0], .4, places=6)
        self.assertAlmostEqual(report['points_in_anchor'][0][1], 0., places=6)
        self.assertTrue(any(j >= 2 and w > .5 for j, w in new[6][18]))
        for row in new[6]: self.assertAlmostEqual(sum(w for j, w in row), 1., places=6)
        # A translated/rotated/scaled anchor yields the identical bind deformation.
        anchor = [0, 2, 0, 0, -2, 0, 0, 0, 0, 0, 2, 0, 3, 4, 5, 1]
        for i, p in enumerate(report['points_in_anchor']):
            expected = H.multiply(anchor, old[7][1]); actual = H.multiply(H.multiply(anchor, H.translation(p)), new[7][2 + i])
            self.assertLess(max(abs(a - b) for a, b in zip(actual, expected)), 1e-6)
        stored = after.doc['nodes'][4]['extras']['has_generated_helper']['authoring']; self.assertEqual(stored['source_sha256'], self.g.sha)
    def test_deterministic_output_and_correctable_points(self):
        plan = request(self.g); plan['points_in_anchor'] = [[.4, 0, .1], [.4, -.36, .1], [.4, -.72, .1], [.4, -1.08, .1]]
        a = H.build(self.path, self.root / 'a', plan); b = H.build(self.path, self.root / 'b', plan)
        self.assertEqual(Path(a['glb']).read_bytes(), Path(b['glb']).read_bytes()); self.assertEqual(a['report']['points_in_anchor'], [tuple(p) for p in plan['points_in_anchor']])
    def test_quantized_and_eight_weight_layouts(self):
        for i, (quantized, eight) in enumerate([(True, False), (False, True)]):
            path = self.root / (str(i) + '.glb'); g = fixture(path, quantized, eight)
            result = H.build(path, self.root / ('out' + str(i)), request(g)); new = H.GLB(result['glb'])
            self.assertEqual(new.skin(3, 1)[6][20:], g.skin(3, 1)[6][20:])
            self.assertEqual('JOINTS_1' in new.skin(3, 1)[2]['attributes'], eight)
    def test_transfer_can_add_an_eight_weight_set_without_pruning_other_joints(self):
        source = self.root / 'mixed.glb'; g = mixed_fixture(source); value = H.build(source, self.root / 'mixed-output', request(g)); derived = H.GLB(value['glb'])
        self.assertIn('JOINTS_1', derived.skin(3, 1)[2]['attributes'])
        before = g.skin(3, 1)[6]; after = derived.skin(3, 1)[6]
        for a, b in zip(before, after):
            self.assertEqual(dict(a)[0], dict(b)[0]); self.assertEqual(dict(a)[2], dict(b)[2])
        self.assertTrue(any(len(row) == 5 for row in after))
    def test_full_eight_influences_refuse_without_pruning_or_writing(self):
        source = self.root / 'full-eight.glb'; g = fixture(source)
        for i in range(6):
            g.doc['skins'][0]['joints'].append(len(g.doc['nodes']))
            g.doc['nodes'][1]['children'].append(len(g.doc['nodes']))
            g.doc['nodes'].append({'name': 'Existing weighted joint ' + str(i)})
        g.doc['skins'][0]['inverseBindMatrices'] = g.append([H.IDENTITY, H.translation((0, -2, 0))] + [H.IDENTITY] * 6, 'MAT4')
        attrs = g.doc['meshes'][0]['primitives'][1]['attributes']
        for slot in range(2):
            attrs['JOINTS_' + str(slot)] = g.append([tuple(range(slot * 4, slot * 4 + 4))] * 24, 'VEC4', 5121)
            attrs['WEIGHTS_' + str(slot)] = g.append([(.125,) * 4] * 24, 'VEC4')
        write_glb(source, g.doc, bytes(g.binary)); g = H.GLB(source)
        before = (source.read_bytes(), source.stat().st_mtime_ns)
        with self.assertRaisesRegex(ValueError, 'exceed8influences'):
            H.build(source, self.root / 'refused-eight', request(g))
        self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)
        self.assertFalse((self.root / 'refused-eight').exists())
    def test_preview_is_bounded_and_matches_exact_selected_skin_coordinates(self):
        value = H.preview(self.path, request(self.g))
        self.assertEqual(len(value['vertices']), 20); self.assertEqual(len(value['points_in_anchor']), 4)
        self.assertEqual(value['region']['anchor_node'], 2)
        self.assertEqual([a['available'] for a in value['anchors']], [False, True])
        invalid = request(self.g); invalid['anchor_node'] = 1
        with self.assertRaisesRegex(ValueError, 'no usable weights'): H.preview(self.path, invalid)
        positions = self.g.skin(3, 1)[4]
        for v, influences in enumerate(value['vertices']):
            self.assertEqual(len(influences), 1); self.assertEqual(influences[0][0], 2)
            expected = H.point(H.translation((0, -2, 0)), positions[v]); self.assertEqual(tuple(influences[0][1:4]), expected)
        self.assertTrue(all(0 <= a < 20 and 0 <= b < 20 for a, b in value['edges']))
    def test_tiny_long_shape_is_not_suggested_from_aspect_alone(self):
        g = self.g; attrs = g.doc['meshes'][0]['primitives'][1]['attributes']; positions = g.accessor(attrs['POSITION'], 'VEC3')
        for i in range(20): positions[i] = (.4 + (positions[i][0] - .4) * .01, 2 + (positions[i][1] - 2) * .01, .1)
        attrs['POSITION'] = g.append(positions, 'VEC3'); path = self.root / 'tiny.glb'; write_glb(path, g.doc, bytes(g.binary))
        rows = H.inspect(path)['regions']; row = next(v for v in rows if v['primitive'] == 1 and v['component'] == 0)
        self.assertGreater(row['elongation'], 2); self.assertLess(row['length_relative_to_rig'], .06); self.assertFalse(row['suggested'])
    def test_refuses_unreviewed_stale_or_degenerate_plan_without_output(self):
        for changes in [{'reviewed': False}, {'source_sha256': '0' * 64}, {'component': 99}, {'anchor_node': 99}, {'strength': math.nan}, {'segments': 0}, {'segments': 9}, {'points_in_anchor': [[0, 0, 0]] * 4}]:
            plan = request(self.g); plan.update(changes)
            with self.assertRaises((ValueError, TypeError)): H.build(self.path, self.root / 'no', plan)
            self.assertFalse((self.root / 'no').exists())
    def test_existing_springs_and_output_preserve_previous_assets(self):
        original = self.path.read_bytes(); self.root.joinpath('previous').mkdir(); marker = self.root / 'previous' / 'keep'; marker.write_text('owner data')
        with self.assertRaises(ValueError): H.build(self.path, self.root / 'previous', request(self.g))
        self.assertEqual(marker.read_text(), 'owner data'); self.assertEqual(self.path.read_bytes(), original)
        doc = copy.deepcopy(self.g.doc); doc['extensions'] = {'VRMC_springBone': {'specVersion': '1.0', 'springs': [{'joints': [{'node': 1}, {'node': 2}]}]}}
        path = self.root / 'native.glb'; write_glb(path, doc, bytes(self.g.binary)); g = H.GLB(path)
        self.assertTrue(H.inspect(path)['existing_springs'])
        with self.assertRaisesRegex(ValueError, 'already uses'): H.build(path, self.root / 'no', request(g))
        self.assertFalse((self.root / 'no').exists())
    def test_second_region_preserves_first_chain_weights_and_refuses_overlap(self):
        path = self.root/'panels.glb'; g = two_panel_fixture(path)
        first = H.build(path, self.root/'first', request(g)); a = H.GLB(first['glb'])
        plan = request(a); plan['component'] = 1
        second = H.build(a.source, self.root/'second', plan); b = H.GLB(second['glb'])
        self.assertEqual(len(b.springs()), 2)
        self.assertEqual(b.doc['extras']['has_secondary_helpers_1']['springs'][0], a.doc['extras']['has_secondary_helpers_1']['springs'][0])
        self.assertEqual(a.skin(3,1)[6][:20], b.skin(3,1)[6][:20])
        self.assertTrue(bytes(b.binary).startswith(a.binary))
        rows = H.inspect(b.source)['regions']; self.assertTrue(all(r['already_rigged'] for r in rows if r['primitive']==1))
        with self.assertRaisesRegex(ValueError,'already uses'): H.build(b.source,self.root/'overlap',request(b))
        self.assertFalse((self.root/'overlap').exists())
    def test_native_v0_v1_coexist_without_shadowing_or_rewriting(self):
        for family in ['v0','v1']:
            path = self.root/(family+'.glb'); g = two_panel_fixture(path,family); before = copy.deepcopy(g.doc['extensions'])
            value = H.build(path,self.root/(family+'-derived'),request(g)); derived = H.GLB(value['glb'])
            self.assertEqual(derived.doc['extensions'], before)
            self.assertEqual(len(derived.springs()),2); self.assertEqual(derived.spring_nodes(),{4,5,6,7,8,9})
            self.assertEqual(derived.doc['nodes'][:4],g.doc['nodes'][:2]+[dict(g.doc['nodes'][2],children=[4,6])]+g.doc['nodes'][3:4])
    def test_older_generated_vrmc_metadata_remains_augmentable(self):
        path=self.root/'old.glb';g=two_panel_fixture(path);first=H.build(path,self.root/'old-first',request(g));a=H.GLB(first['glb'])
        old=a.doc.pop('extras')['has_secondary_helpers_1'];a.doc['extensions']={'VRMC_springBone':old};write_glb(a.source,a.doc,bytes(a.binary));a=H.GLB(a.source)
        plan=request(a);plan['component']=1;value=H.build(a.source,self.root/'old-next',plan);b=H.GLB(value['glb'])
        self.assertEqual(b.doc['extensions']['VRMC_springBone'],old);self.assertEqual(len(b.springs()),2)
    def test_patch_pins_cut_boundary_and_preserves_surrounding_skin(self):
        mask=list(range(8,20)); derived,report=self.build(vertex_mask=mask)
        self.assertEqual(report['region']['vertex_mask'],mask)
        self.assertEqual(report['region']['attachment_method'],'pinned cut boundary')
        self.assertEqual(report['region']['attachment_vertices'],2)
        old=self.g.skin(3,1);new=derived.skin(3,1)
        self.assertEqual(old[6][:10],new[6][:10]);self.assertEqual(old[6][20:],new[6][20:])
        self.assertTrue(any(j>=2 for j,w in new[6][18]))
        p=H.preview(self.path,dict(request(self.g),vertex_mask=mask))
        self.assertEqual(p['source_vertices'],list(range(20)));self.assertEqual(p['selected_vertices'],mask)
        self.assertTrue(all(a in mask and b in mask for a,b in p['edges']))
    def test_partly_rigged_component_can_review_a_disjoint_unrigged_patch(self):
        first=H.build(self.path,self.root/'lower',dict(request(self.g),vertex_mask=list(range(8,20))));g=H.GLB(first['glb'])
        rows=H.inspect(g.source)['regions'];self.assertTrue(next(r for r in rows if r['primitive']==1 and r['component']==0)['already_rigged'])
        view=H.preview(g.source,dict(request(g),review_only=True));self.assertFalse(view['can_apply'])
        plan=dict(request(g),vertex_mask=list(range(8)));view=H.preview(g.source,plan);self.assertTrue(view['can_apply'])
        second=H.build(g.source,self.root/'upper',plan);b=H.GLB(second['glb']);self.assertEqual(len(b.springs()),2)
        self.assertEqual(g.skin(3,1)[6][8:],b.skin(3,1)[6][8:])
        with self.assertRaisesRegex(ValueError,'already uses'):H.build(g.source,self.root/'overlap-patch',dict(request(g),vertex_mask=list(range(10,20))))
    def test_invalid_patch_refuses_without_creating_outputs(self):
        for mask in [[],[True,1,2],[0,0,1],[0,1,9999],[0,1,20],[0,1,2,16,17,18],[0,1,2]]:
            with self.assertRaises(ValueError):H.build(self.path,self.root/'bad-patch',dict(request(self.g),vertex_mask=mask))
            self.assertFalse((self.root/'bad-patch').exists())
    def test_derived_json_budget_refuses_before_creating_an_unreadable_asset(self):
        path=self.root/'large-metadata.glb';g=fixture(path)
        size=len(json.dumps(g.doc,separators=(',',':'),ensure_ascii=True).encode())
        g.doc['extras']={'original_padding':'x'*(H.MAX_JSON-size-512)};write_glb(path,g.doc,bytes(g.binary));g=H.GLB(path)
        with self.assertRaisesRegex(ValueError,'Derived GLB JSON'):H.build(path,self.root/'oversized-derived',request(g))
        self.assertFalse((self.root/'oversized-derived').exists())
    def test_generated_bind_range_matches_the_reader_contract(self):
        points=[[0,100000-i,0] for i in range(4)]
        with self.assertRaisesRegex(ValueError,'coordinate range'):self.build(points_in_anchor=points)
        self.assertFalse((self.root/'derived').exists())
    def test_native_index_bindings_and_embedded_animation_remain_intact(self):
        doc = copy.deepcopy(self.g.doc)
        doc['extensions'] = {'VRM': {'blendShapeMaster': {'blendShapeGroups': [{'binds': [{'mesh': 0, 'index': 0, 'weight': 100}]}]}}}
        g0 = fixture(self.root / 'animated.glb')
        time_accessor = g0.append([(0.,), (1.,)], 'SCALAR'); rotation_accessor = g0.append([(0., 0., 0., 1.), (0., 0., .1, math.sqrt(.99))], 'VEC4')
        doc = g0.doc; doc['extensions'] = {'VRM': {'blendShapeMaster': {'blendShapeGroups': [{'binds': [{'mesh': 0, 'index': 0, 'weight': 100}]}]}}}
        doc['animations'] = [{'name': 'retained native action', 'samplers': [{'input': time_accessor, 'output': rotation_accessor}], 'channels': [{'sampler': 0, 'target': {'node': 2, 'path': 'rotation'}}]}]
        path = self.root / 'native-data.glb'; write_glb(path, doc, bytes(g0.binary)); g = H.GLB(path)
        value = H.build(path, self.root / 'native-data-derived', request(g)); derived = H.GLB(value['glb'])
        self.assertEqual(derived.doc['extensions']['VRM'], doc['extensions']['VRM']); self.assertEqual(derived.doc['animations'], doc['animations'])
        self.assertEqual(derived.doc['nodes'][3]['mesh'], 0); self.assertEqual(derived.doc['meshes'][0]['primitives'][1]['targets'], doc['meshes'][0]['primitives'][1]['targets'])
        doc['nodes'].append({'mesh': 0, 'skin': 0}); path = self.root / 'shared.glb'; write_glb(path, doc, bytes(g0.binary)); g = H.GLB(path)
        with self.assertRaisesRegex(ValueError, 'shared'): H.build(path, self.root / 'shared-output', request(g))
        self.assertFalse((self.root / 'shared-output').exists())
    def test_external_and_accessor_corruption_refuse_before_writes(self):
        for i, mutate in enumerate([lambda d: d['images'][0].update({'uri': '../private.png'}), lambda d: d['accessors'][d['meshes'][0]['primitives'][1]['attributes']['POSITION']].update({'count': 100001}), lambda d: d['bufferViews'][0].update({'byteLength': 99999999})]):
            doc = copy.deepcopy(self.g.doc); mutate(doc); path = self.root / ('bad' + str(i) + '.glb'); write_glb(path, doc, bytes(self.g.binary))
            with self.assertRaises(ValueError):
                g = H.GLB(path); H.build(path, self.root / 'no', request(g))
            self.assertFalse((self.root / 'no').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
