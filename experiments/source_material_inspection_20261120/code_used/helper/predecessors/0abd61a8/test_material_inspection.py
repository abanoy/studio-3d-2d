"""Unrun fake RNA/library tests; no native assets, Blender or image decoding."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from types import SimpleNamespace as NS
import unittest
import zlib

import material_inspection as inspection

# Import only the reviewed stdlib-only enumeration definitions, never its main.
ENUM_PATH = Path(__file__).absolute().parents[1] / 'source-material-library-prep-20261120/library_worker.py'
_spec = importlib.util.spec_from_file_location('_material_inspection_test_enumeration', ENUM_PATH)
enumeration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(enumeration)


def png(width=2, height=3):
    # Header fixture only, deliberately not a pixel/decode or full PNG oracle.
    ihdr = b'IHDR' + struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + ihdr + struct.pack('>I', zlib.crc32(ihdr))


class ID:
    def __init__(self, name, pointer, library=None):
        self.name = self.name_full = name
        self.pointer, self.library, self.original = pointer, library, self
    def as_pointer(self): return self.pointer


class PackedFile:
    def __init__(self, raw):
        self.raw, self.size, self.reads, self.on_read = raw, len(raw), 0, None
    @property
    def data(self):
        self.reads += 1
        if self.on_read: self.on_read()
        return self.raw


class ImagePackedFile:
    def __init__(self, packed): self.packed_file = packed


class Image(ID):
    def __init__(self, name, pointer):
        super().__init__(name, pointer)
        self.source, self.type, self.filepath = 'FILE', 'IMAGE', 'C:/inert/private/source.vtf'
        self.packed_file = PackedFile(png())
        self.packed_files = [ImagePackedFile(self.packed_file)]
        self.forbidden_getters = 0
    def forbidden(self):
        self.forbidden_getters += 1
        raise AssertionError('Image buffers/dimensions MUST NOT be read')
    size = property(forbidden)
    channels = property(forbidden)
    pixels = property(forbidden)
    has_data = property(forbidden)
    filepath_raw = property(forbidden)


class NodeSocket:
    def __init__(self, node, name, default=None):
        self.node, self.id_data, self.identifier, self.name = node, node.id_data, name, name
        self.default_value = default


class Sockets(list):
    def __getitem__(self, key):
        if type(key) is str:
            return next(socket for socket in self if socket.identifier == key)
        return super().__getitem__(key)


class Node:
    def __init__(self, tree, name):
        self.id_data, self.name, self.mute = tree, name, False
        self.inputs, self.outputs = Sockets(), Sockets()


class ShaderNodeOutputMaterial(Node):
    def __init__(self, tree):
        super().__init__(tree, 'Output')
        self.is_active_output, self.target = True, 'ALL'
        self.inputs.append(NodeSocket(self, 'Surface'))


class ShaderNodeBsdfPrincipled(Node):
    def __init__(self, tree):
        super().__init__(tree, 'Principled')
        self.inputs.extend([NodeSocket(self, 'Base Color', (1., .5, .25, 1.)),
                            NodeSocket(self, 'Alpha', 1.), NodeSocket(self, 'Roughness', .5)])
        self.outputs.append(NodeSocket(self, 'BSDF'))


class ShaderNodeTexImage(Node):
    def __init__(self, tree, image):
        super().__init__(tree, 'Texture')
        self.image = image
        self.interpolation, self.extension, self.projection = 'Linear', 'REPEAT', 'FLAT'
        self.inputs.append(NodeSocket(self, 'Vector', (0., 0., 0.)))
        self.outputs.extend([NodeSocket(self, 'Color'), NodeSocket(self, 'Alpha')])


class NodeLink:
    def __init__(self, tree, source, destination):
        self.id_data, self.is_valid = tree, True
        self.from_socket, self.to_socket = source, destination
        self.from_node, self.to_node = source.node, destination.node


class ShaderNodeTree(ID):
    def __init__(self, pointer, image):
        super().__init__('Embedded tree', pointer)
        self.is_embedded_data, self.animation_data = True, None
        output, shader = ShaderNodeOutputMaterial(self), ShaderNodeBsdfPrincipled(self)
        self.nodes = [output, shader]
        self.links = [NodeLink(self, shader.outputs['BSDF'], output.inputs['Surface'])]
        if image is not None:
            texture = ShaderNodeTexImage(self, image); self.nodes.append(texture)
            self.links.extend([NodeLink(self, texture.outputs['Color'], shader.inputs['Base Color']),
                               NodeLink(self, texture.outputs['Alpha'], shader.inputs['Alpha'])])


class Material(ID):
    def __init__(self, name, pointer, image=None):
        super().__init__(name, pointer)
        self.use_nodes, self.use_backface_culling, self.animation_data = True, False, None
        self.node_tree = ShaderNodeTree(pointer + 1000, image)


class LibraryView:
    def __init__(self, values): object.__setattr__(self, 'values', values)
    def __dir__(self): return list(self.values)
    def __getattr__(self, key): return self.values[key]
    def __setattr__(self, key, value): self.values[key] = value


class Libraries(list):
    def load(self, path, *, link):
        if link is not False: raise AssertionError('Only explicit append mode is admitted')
        self.calls.append((path, link))
        return self.context


class FakeContext:
    def __init__(self, fixture):
        self.f = fixture
        self.source = LibraryView(dict(materials=list(fixture.names), images=['private image catalogue'],
                                       objects=['private historical object'], libraries=[], node_groups=[], version=(5, 1, 0)))
        self.destination = LibraryView({key: [] for key in self.source.values if key != 'version'} | {'version': (5, 1, 0)})
        self.exited, self.failure, self.after = 0, None, None
    def __enter__(self): return self.source, self.destination
    def __exit__(self, *_args):
        self.exited += 1
        self.f.submitted = self.destination.materials
        # Mimic C API: strings replaced in this SAME list by actual returned IDs.
        for index, material in enumerate(self.f.materials): self.destination.materials[index] = material
        self.f.bpy.data.materials.extend(self.f.materials)
        self.f.bpy.data.images.extend(self.f.images)
        if self.after: self.after()
        if self.failure: raise self.failure
        return False


class Fixture:
    def __init__(self, *, textured=True, shared=False):
        self.names = ('Owned A', 'Owned B', 'Owned C', 'Owned D')
        self.images = [Image('private image ' + str(index), 100 + index)
                       for index in range((1 if shared else 4) if textured else 0)]
        self.materials = [Material(name, 200 + index, self.images[0 if shared else index] if textured else None)
                          for index, name in enumerate(self.names)]
        types = NS(ID=ID, Material=Material, Image=Image, ShaderNodeTree=ShaderNodeTree,
                   ShaderNodeOutputMaterial=ShaderNodeOutputMaterial, ShaderNodeBsdfPrincipled=ShaderNodeBsdfPrincipled,
                   ShaderNodeTexImage=ShaderNodeTexImage, NodeLink=NodeLink, NodeSocket=NodeSocket,
                   ImagePackedFile=ImagePackedFile, PackedFile=PackedFile)
        data = NS(materials=[Material('Factory material', 1)], images=[], objects=[ID('Factory object', 2)],
                  libraries=Libraries(), node_groups=[])
        id_type = NS(identifier='ID', base=None)
        data.bl_rna = NS(properties=[NS(identifier=name, type='COLLECTION', fixed_type=NS(identifier=name, base=id_type))
                                      for name in ('materials', 'images', 'objects', 'libraries', 'node_groups')])
        self.bpy = NS(types=types, data=data)
        self.context = FakeContext(self)
        data.libraries.calls, data.libraries.context = [], self.context
    def run(self):
        return inspection.inspect_material_library(self.bpy, 'owned-authenticated-path', self.names, enumeration)
    def refused(self, test, code):
        with test.assertRaisesRegex(inspection.Refusal, '^' + code + '$') as caught:
            self.run()
        result = caught.exception.summary
        test.assertEqual(result['status'], 'REFUSED')
        return result


class InspectionTests(unittest.TestCase):
    def test_exact_returned_refs_order_graphs_and_single_packed_copies(self):
        f = Fixture(); result = f.run(); summary = result['summary']
        self.assertTrue(all(actual is expected for actual, expected in zip(result['materials'], f.materials)))
        self.assertTrue(all(actual is expected for actual, expected in zip(f.submitted, f.materials)))
        self.assertEqual(summary['added_id_counts'], {'images': 4, 'materials': 4})
        self.assertEqual((summary['before_id_count'], summary['after_id_count']), (2, 10))
        self.assertTrue(summary['surviving_originals_unchanged'])
        self.assertEqual(summary['inspected_material_graphs'], 4)
        self.assertEqual(summary['reached_images'], 4)
        self.assertEqual(summary['packed_bytes_copied'], 4 * len(png()))
        self.assertEqual(summary['prospective_rgba_f32_bytes'], 4 * 2 * 3 * 16)
        self.assertTrue(all(image.packed_file.reads == 1 and image.forbidden_getters == 0 for image in f.images))
        self.assertEqual(f.bpy.data.libraries.calls, [('owned-authenticated-path', False)])

    def test_public_summary_exposes_no_names_paths_references_or_bytes(self):
        f = Fixture(); summary = f.run()['summary']; encoded = json.dumps(summary)
        for forbidden in ('Owned A', 'private image', 'Factory material', 'owned-authenticated-path', 'source.vtf'):
            self.assertNotIn(forbidden, encoded)
        for key, value in summary.items():
            if key.endswith('_qualified'): self.assertIs(value, False, key)
        self.assertFalse(summary['image_buffer_getters_used'])
        self.assertFalse(summary['external_filepath_retrieval_attempted'])

    def test_solid_materials_need_no_images_and_shared_images_are_explicit_relation(self):
        solid = Fixture(textured=False).run()['summary']
        self.assertEqual((solid['reached_images'], solid['packed_bytes_copied']), (0, 0))
        shared = Fixture(shared=True).run()['summary']
        self.assertEqual((shared['reached_images'], shared['shared_image_references']), (1, 3))

    def test_catalogue_mismatch_refuses_before_nonempty_assignment(self):
        f = Fixture(); f.context.source.values['materials'][0] = 'changed catalogue'
        # C exit still executes even for a body exception. A zero-request context
        # should perform no append, so fake that source-defined behavior here.
        class EmptyExit:
            def __enter__(self): return f.context.source, f.context.destination
            def __exit__(self, *_args): return False
        f.bpy.data.libraries.context = EmptyExit()
        summary = f.refused(self, 'EXACT_OWNED_LIBRARY_MATERIAL_CATALOGUE_CHANGED')
        self.assertFalse(summary['append_requested'])
        self.assertEqual(f.context.destination.materials, [])
        self.assertEqual(len(f.bpy.data.materials), 1)

    def test_unexpected_geometry_stays_present_and_refuses_without_cleanup(self):
        f = Fixture(); extra = ID('private unexpected mesh object', 800)
        f.context.after = lambda: f.bpy.data.objects.append(extra)
        summary = f.refused(self, 'UNSUPPORTED_ADDED_ID_CATEGORY')
        self.assertEqual(summary['added_id_counts']['objects'], 1)
        self.assertIs(f.bpy.data.objects[-1], extra)
        self.assertTrue(all(image.packed_file.reads == 0 for image in f.images))

    def test_original_pointer_equal_replacement_or_name_change_refuses(self):
        for replace in (True, False):
            f = Fixture()
            if replace: f.context.after = lambda: f.bpy.data.objects.__setitem__(0, ID('Factory object', 2))
            else: f.context.after = lambda: setattr(f.bpy.data.objects[0], 'name', 'changed')
            summary = f.refused(self, 'PREEXISTING_ID_REFERENCE_OR_METADATA_CHANGED')
            self.assertFalse(summary['surviving_originals_unchanged'])

    def test_returned_list_cannot_be_substituted_even_with_identical_refs(self):
        f = Fixture(); f.context.after = lambda: setattr(f.context.destination, 'materials', list(f.materials))
        f.refused(self, 'RETURNED_REQUEST_LIST_IDENTITY_REQUIRED')

    def test_material_rename_extra_material_and_linked_material_refuse(self):
        for kind, code in (('rename', 'EXACT_NEW_LOCAL_RETURNED_MATERIAL_REFERENCES'),
                           ('extra', 'EXACT_NEW_LOCAL_RETURNED_MATERIAL_REFERENCES'),
                           ('linked', 'EXACT_NEW_LOCAL_RETURNED_MATERIAL_REFERENCES')):
            f = Fixture()
            if kind == 'rename': f.materials[0].name += '.001'
            elif kind == 'extra': f.context.after = lambda: f.bpy.data.materials.append(Material('extra', 900))
            else: f.materials[0].library = ID('foreign library', 901)
            f.refused(self, code)

    def test_nonmaterial_destination_request_is_not_ignored_after_exit(self):
        f = Fixture(); f.context.after = lambda: f.context.destination.values['objects'].append('unexpected')
        f.refused(self, 'UNREQUESTED_DESTINATION_LIST_CHANGED')

    def test_groups_extra_nodes_and_extra_links_refuse_without_shader_edits(self):
        for mode in ('group_id', 'node', 'link'):
            f = Fixture(); tree = f.materials[0].node_tree
            if mode == 'group_id':
                f.context.after = lambda: f.bpy.data.node_groups.append(ShaderNodeTree(700, None))
                code = 'UNSUPPORTED_ADDED_ID_CATEGORY'
            elif mode == 'node': tree.nodes.append(Node(tree, 'Unsupported')); code = 'SIMPLE_COMPLETE_GRAPH_BUDGET'
            else: tree.links.append(tree.links[0]); code = 'SIMPLE_COMPLETE_GRAPH_BUDGET'
            before = tuple(tree.nodes)
            f.refused(self, code)
            self.assertEqual(tuple(tree.nodes), before)
            self.assertTrue(all(image.packed_file.reads == 0 for image in f.images))

    def test_link_and_socket_owners_must_be_actual_tree_references(self):
        f = Fixture(); tree = f.materials[0].node_tree
        tree.links[0].from_socket.id_data = f.materials[1].node_tree
        f.refused(self, 'ACTUAL_CONNECTED_SOCKET_OWNER_REQUIRED')

    def test_nonembedded_or_animated_tree_and_muted_node_are_not_admitted(self):
        for mode, code in (('embedded', 'LOCAL_EMBEDDED_MATERIAL_NODE_TREE_REQUIRED'),
                           ('animation', 'LOCAL_EMBEDDED_MATERIAL_NODE_TREE_REQUIRED'),
                           ('muted', 'UNSUPPORTED_NODE_OR_OWNER_OR_MUTED_GRAPH')):
            f = Fixture(); tree = f.materials[0].node_tree
            if mode == 'embedded': tree.is_embedded_data = False
            elif mode == 'animation': tree.animation_data = object()
            else: tree.nodes[0].mute = True
            f.refused(self, code)

    def test_unreachable_or_preexisting_graph_image_is_not_repaired_by_matching_name(self):
        f = Fixture(); f.images.append(Image('unreachable image', 800))
        f.refused(self, 'UNREACHED_ADDED_IMAGE_DEPENDENCY')
        f = Fixture(); prior = Image(f.images[0].name, 801); f.bpy.data.images.append(prior)
        f.materials[0].node_tree.nodes[2].image = prior
        f.refused(self, 'GRAPH_IMAGE_NOT_NEW_LOCAL_DEPENDENCY')

    def test_external_viewer_multiple_parts_and_broken_packed_alias_refuse_before_copy(self):
        for mode, code in (('external', 'EXACT_SINGLE_CONNECTED_PACKED_FILE_REQUIRED'),
                           ('viewer', 'PACKED_FILE_IMAGE_PROFILE_REQUIRED'),
                           ('multiple', 'EXACT_SINGLE_CONNECTED_PACKED_FILE_REQUIRED'),
                           ('alias', 'EXACT_SINGLE_CONNECTED_PACKED_FILE_REQUIRED')):
            f = Fixture(); image = f.images[0]
            if mode == 'external': image.packed_file = None
            elif mode == 'viewer': image.source, image.type = 'VIEWER', 'COMPOSITING'
            elif mode == 'multiple': image.packed_files.append(ImagePackedFile(PackedFile(png())))
            else: image.packed_files[0].packed_file = PackedFile(png())
            original_files = [im.packed_files[0].packed_file for im in f.images]
            f.refused(self, code)
            self.assertTrue(all(packed.reads == 0 for packed in original_files))

    def test_every_packed_size_is_checked_before_first_byte_copy(self):
        f = Fixture(); f.images[-1].packed_file.size = inspection.MAX_ENCODED_BYTES + 1
        f.refused(self, 'PACKED_ENCODED_SIZE_BUDGET')
        self.assertTrue(all(image.packed_file.reads == 0 for image in f.images))
        f = Fixture()
        for image in f.images[:3]: image.packed_file.size = inspection.MAX_ENCODED_BYTES
        f.refused(self, 'AGGREGATE_PACKED_ENCODED_BUDGET')
        self.assertTrue(all(image.packed_file.reads == 0 for image in f.images))

    def test_size_boolean_or_inexact_copy_is_not_coerced(self):
        f = Fixture(); f.images[0].packed_file.size = True
        f.refused(self, 'PACKED_ENCODED_SIZE_BUDGET')
        f = Fixture(); f.images[0].packed_file.raw += b'extra'
        f.refused(self, 'EXACT_PACKED_BYTE_COPY_REQUIRED')

    def test_png_header_crc_and_prospective_dimensions_refuse_without_decoder(self):
        f = Fixture(); raw = bytearray(png()); raw[-1] ^= 1; f.images[0].packed_file.raw = bytes(raw)
        f.refused(self, 'PNG_SIGNATURE_IHDR_OR_CRC_REQUIRED')
        f = Fixture(); f.images[0].packed_file.raw = png(16384, 16384)
        f.refused(self, 'PNG_HEADER_OR_PROSPECTIVE_RGBA_F32_BUDGET')
        self.assertTrue(all(image.forbidden_getters == 0 for image in f.images))

    def test_aggregate_prospective_rgba_budget_is_separate_from_encoded_size(self):
        f = Fixture()
        for image in f.images: image.packed_file.raw = png(3000, 1000)
        f.refused(self, 'AGGREGATE_PROSPECTIVE_RGBA_F32_BUDGET')
        self.assertEqual(sum(image.packed_file.reads for image in f.images), 3)
        self.assertTrue(all(image.forbidden_getters == 0 for image in f.images))

    def test_graph_or_census_mutation_during_read_is_detected_and_recorded(self):
        f = Fixture()
        f.images[0].packed_file.on_read = lambda: setattr(f.materials[0].node_tree.nodes[1].inputs['Alpha'], 'default_value', .25)
        f.refused(self, 'GRAPH_CHANGED_DURING_INSPECTION')
        f = Fixture()
        f.images[0].packed_file.on_read = lambda: setattr(f.bpy.data.objects[0], 'name', 'late mutation')
        summary = f.refused(self, 'ID_CENSUS_CHANGED_DURING_INSPECTION')
        self.assertFalse(summary['surviving_originals_unchanged'])

    def test_context_exit_failure_retains_actual_surviving_census_and_safe_error(self):
        f = Fixture(); f.context.failure = RuntimeError('private raw error must not leak')
        summary = f.refused(self, 'MATERIAL_INSPECTION_API_REFUSAL')
        self.assertTrue(summary['append_requested'])
        self.assertFalse(summary['append_completed'])
        self.assertEqual(summary['added_id_counts'], {'images': 4, 'materials': 4})
        self.assertNotIn('private raw error', json.dumps(summary))

    def test_invalid_request_names_refuse_before_native_context(self):
        f = Fixture()
        for names in (list(f.names), f.names[:3], ('same',) * 4, ('', 'B', 'C', 'D')):
            with self.assertRaises(inspection.Refusal):
                inspection.inspect_material_library(f.bpy, 'owned', names, enumeration)
        self.assertEqual(f.bpy.data.libraries.calls, [])


if __name__ == '__main__':
    unittest.main()
