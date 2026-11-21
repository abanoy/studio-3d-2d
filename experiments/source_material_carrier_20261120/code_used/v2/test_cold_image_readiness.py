"""Pure fake-RNA ordering/identity tests; never import bpy or native assets.

The 33-byte IHDR fixtures test admission, not a real PNG decoder. Root owns
actual cold-buffer and export qualification. Every fake image-buffer access is
observable; forbidden pixels/file_format getters raise immediately.
"""
import hashlib
import importlib.util
from pathlib import Path
import struct
import types
import unittest
import zlib


HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load('cold_readiness_under_test', 'cold_image_readiness.py')
I = load('cold_readiness_pinned_inspector', 'material_inspection.py')


def png(width=8, height=4, color=6):
    body = b'IHDR' + struct.pack('>IIBBBBB', width, height, 8, color, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + body + struct.pack('>I', zlib.crc32(body))


class PackedFile:
    def __init__(self, image):
        self.image = image

    @property
    def id_data(self):
        return self.image.packed_owner or self.image

    def as_pointer(self):
        return self.image.packed_pointer

    @property
    def size(self):
        self.image.events.append(('packed_size', self.image.name))
        return self.image.encoded_size

    @property
    def data(self):
        self.image.events.append(('packed_data', self.image.name))
        if self.image.on_data is not None:
            self.image.on_data(self.image)
        return self.image.raw


class ImagePackedFile:
    def __init__(self, image):
        self.image = image

    @property
    def id_data(self):
        return self.image.part_owner or self.image

    def as_pointer(self):
        return self.image.part_pointer

    @property
    def packed_file(self):
        return PackedFile(self.image)

    @property
    def view(self):
        return self.image.packed_view

    @property
    def tile_number(self):
        return self.image.packed_tile

    @property
    def filepath(self):
        return self.image.part_path


class UDIMTile:
    def __init__(self, image):
        self.image = image

    @property
    def id_data(self):
        return self.image.tile_owner or self.image

    def as_pointer(self):
        return self.image.tile_pointer

    @property
    def number(self):
        return self.image.tile_number

    @property
    def size(self):
        raise AssertionError('tile size must not be used')

    @property
    def channels(self):
        raise AssertionError('tile channels must not be used')


class Image:
    def __init__(self, name, events, width=8, height=4):
        self.name = name
        self.events = events
        self.original = self
        self.library = None
        self.pointer = 1000 + len(events) + id(self) % 10000000
        self.source = 'FILE'
        self.type = 'IMAGE'
        self.is_dirty = False
        self.animation_data = None
        self.filepath = self.filepath_raw = name + '.png'
        self.is_multiview = self.use_multiview = False
        self.alpha_mode = 'STRAIGHT'
        self.colorspace_settings = types.SimpleNamespace(name='sRGB')
        self.tile_count = self.part_count = 1
        self.tile_number = self.packed_tile = 1001
        self.packed_view = 0
        self.tile_pointer, self.part_pointer, self.packed_pointer = self.pointer + 1, self.pointer + 2, self.pointer + 3
        self.tile_owner = self.part_owner = self.packed_owner = None
        self.part_path = name + '.png'
        self.raw = png(width, height)
        self.encoded_size = len(self.raw)
        self.dimensions = (width, height)
        self.channel_count = 4
        self.loaded = False
        self.load_on_size = True
        self.on_size = self.on_data = None

    def as_pointer(self):
        return self.pointer

    @property
    def tiles(self):
        return [UDIMTile(self) for _ in range(self.tile_count)]

    @property
    def packed_files(self):
        return [ImagePackedFile(self) for _ in range(self.part_count)]

    @property
    def packed_file(self):
        return PackedFile(self)

    @property
    def has_data(self):
        return self.loaded

    @property
    def size(self):
        self.events.append(('buffer_size', self.name))
        if self.load_on_size:
            self.loaded = True
        if self.on_size is not None:
            self.on_size(self)
        return self.dimensions

    @property
    def channels(self):
        self.events.append(('buffer_channels', self.name))
        return self.channel_count

    @property
    def pixels(self):
        raise AssertionError('pixels getter must not be used')

    @property
    def file_format(self):
        raise AssertionError('file_format getter must not be used')


BPY = types.SimpleNamespace(types=types.SimpleNamespace(Image=Image, PackedFile=PackedFile,
    ImagePackedFile=ImagePackedFile, UDIMTile=UDIMTile))


def ticket(image):
    part, packed = image.packed_files[0], image.packed_file
    return dict(image=image, packed_part=part, packed=packed, name=image.name,
        filepath=image.filepath, encoded_bytes=image.encoded_size,
        encoded_sha256=hashlib.sha256(image.raw).hexdigest(), width=image.dimensions[0],
        height=image.dimensions[1], packed_part_key=I._nonid_key(part, ImagePackedFile, image),
        packed_key=I._nonid_key(packed, PackedFile, image))


class ColdReadinessTests(unittest.TestCase):
    def setUp(self):
        self.events = []

    def image(self, name='image', width=8, height=4):
        return Image(name, self.events, width, height)

    def refused(self, rows):
        with self.assertRaises(C.Refusal) as caught:
            C.acquire_packed_png_buffers(BPY, tuple(rows), I)
        self.assertEqual(caught.exception.summary['status'], 'REFUSED')
        self.assertFalse(caught.exception.summary['resource_equivalence_qualified'])
        self.assertFalse(caught.exception.summary['exporter_qualified'])
        return caught.exception

    def no_buffers(self):
        self.assertFalse(any(kind.startswith('buffer_') for kind, _ in self.events))

    def test_cold_success_returns_actual_refs_exact_resource_tickets_and_honest_scope(self):
        a, b = self.image('a'), self.image('b')
        rows = (ticket(a), ticket(b))
        snapshots = tuple(dict(row) for row in rows)
        actual, summary = C.acquire_packed_png_buffers(BPY, rows, I)
        self.assertIs(actual[0]['image'], a)
        self.assertIs(actual[1]['image'], b)
        self.assertEqual(set(actual[0]), {'image', 'packed_sha256', 'encoded_bytes'})
        self.assertEqual(summary['status'], 'BOUNDED_PACKED_PNG_BUFFERS_READY_1')
        self.assertEqual(summary['initially_unloaded_images'], 2)
        self.assertEqual(summary['images_verified_ready'], 2)
        self.assertEqual(summary['size_getter_attempts'], 2)
        self.assertEqual(summary['channel_getter_attempts'], 2)
        self.assertEqual(sum(k == 'buffer_size' for k, _ in self.events), 2)
        self.assertTrue(summary['complete_set_admitted_before_buffer_getters'])
        self.assertTrue(summary['nonbuffer_metadata_and_packed_refs_unchanged'])
        self.assertTrue(summary['C_encoded_image_decode_may_occur'])
        self.assertFalse(summary['C_external_access_absence_proven'])
        self.assertFalse(summary['python_image_pixels_getter_used'])
        self.assertFalse(summary['cached_pixel_provenance_qualified'])
        self.assertEqual(rows, snapshots)

    def test_already_loaded_buffer_is_counted_without_claiming_pixel_provenance(self):
        a = self.image(); a.loaded = True
        _, summary = C.acquire_packed_png_buffers(BPY, (ticket(a),), I)
        self.assertEqual(summary['initially_loaded_images'], 1)
        self.assertEqual(summary['initially_unloaded_images'], 0)
        self.assertFalse(summary['cached_pixel_provenance_qualified'])

    def test_fresh_non_id_wrappers_with_same_actual_owner_pointer_are_admitted(self):
        a = self.image()
        self.assertIsNot(a.packed_file, a.packed_file)
        self.assertIsNot(a.packed_files[0], a.packed_files[0])
        self.assertIsNot(a.tiles[0], a.tiles[0])
        C.acquire_packed_png_buffers(BPY, (ticket(a),), I)

    def test_all_headers_precede_first_buffer_acquisition(self):
        a, b = self.image('a'), self.image('b')
        C.acquire_packed_png_buffers(BPY, (ticket(a), ticket(b)), I)
        first_buffer = next(n for n, (kind, _) in enumerate(self.events) if kind.startswith('buffer_'))
        prefix = self.events[:first_buffer]
        self.assertIn(('packed_data', 'a'), prefix)
        self.assertIn(('packed_data', 'b'), prefix)

    def test_all_encoded_sizes_precede_first_data_getter(self):
        a, b = self.image('a'), self.image('b')
        rows = [ticket(a), ticket(b)]
        b.encoded_size += 1
        self.refused(rows)
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))
        self.no_buffers()

    def test_aggregate_encoded_budget_refuses_before_any_packed_data(self):
        images = [self.image(str(n)) for n in range(3)]
        for image in images: image.encoded_size = C.MAX_ENCODED_BYTES
        rows = [ticket(image) for image in images]
        self.refused(rows)
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))
        self.no_buffers()

    def test_aggregate_prospective_budget_refuses_before_any_buffer(self):
        images = [self.image(str(n), 2048, 2048) for n in range(3)]
        self.refused([ticket(image) for image in images])
        self.no_buffers()

    def test_per_image_prospective_budget_refuses_before_data_or_buffers(self):
        a = self.image(width=3000, height=3000)
        self.refused([ticket(a)])
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))
        self.no_buffers()

    def test_bad_ihdr_crc_refuses_before_any_buffer(self):
        a = self.image(); a.raw = a.raw[:-1] + bytes([a.raw[-1] ^ 1])
        self.refused([ticket(a)])
        self.no_buffers()

    def test_authenticated_hash_change_refuses_before_any_buffer(self):
        a = self.image(); row = ticket(a); row['encoded_sha256'] = '0' * 64
        self.refused([row])
        self.no_buffers()

    def test_duplicate_actual_image_ticket_refuses_before_payload_or_buffers(self):
        a = self.image(); row = ticket(a)
        self.refused([row, dict(row)])
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))
        self.no_buffers()

    def test_foreign_image_class_is_not_traversed(self):
        class Foreign:
            @property
            def original(self): raise AssertionError('foreign getter touched')
        a = self.image(); row = ticket(a); row['image'] = Foreign()
        row['packed_part_key'] = (ImagePackedFile, id(row['image']), 10)
        row['packed_key'] = (PackedFile, id(row['image']), 11)
        self.refused([row]); self.no_buffers()

    def test_linked_nonoriginal_dirty_or_animated_images_refuse(self):
        for field, value in (('library', object()), ('original', object()),
                             ('is_dirty', True), ('animation_data', object())):
            with self.subTest(field=field):
                a = self.image(field); row = ticket(a); setattr(a, field, value)
                self.refused([row]); self.no_buffers()

    def test_both_multiview_indicators_refuse_without_buffers(self):
        for field in ('is_multiview', 'use_multiview'):
            with self.subTest(field=field):
                a = self.image(field); row = ticket(a); setattr(a, field, True)
                self.refused([row]); self.no_buffers()

    def test_tile_count_number_owner_and_pointer_are_strict(self):
        for field, value in (('tile_count', 2), ('tile_number', 1002), ('tile_number', True),
                             ('tile_owner', object()), ('tile_pointer', 0)):
            with self.subTest(field=field, value=repr(value)):
                a = self.image(field); row = ticket(a); setattr(a, field, value)
                self.refused([row]); self.no_buffers()

    def test_packed_count_view_and_tile_are_strict(self):
        for field, value in (('part_count', 2), ('packed_view', 1), ('packed_view', False),
                             ('packed_tile', 1002), ('packed_tile', True)):
            with self.subTest(field=field, value=value):
                a = self.image(field); row = ticket(a); setattr(a, field, value)
                self.refused([row]); self.no_buffers()

    def test_non_id_owner_and_changed_pointer_refuse_before_data(self):
        for field, value in (('part_owner', object()), ('packed_owner', object()),
                             ('part_pointer', 7), ('packed_pointer', 8)):
            with self.subTest(field=field):
                a = self.image(field); row = ticket(a); setattr(a, field, value)
                self.refused([row]); self.no_buffers()
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))

    def test_same_pointer_foreign_packed_type_is_not_a_value_fallback(self):
        class ForeignPacked(PackedFile):
            @property
            def data(self): raise AssertionError('foreign data getter touched')
        a = self.image(); row = ticket(a); row['packed'] = ForeignPacked(a)
        self.refused([row]); self.no_buffers()

    def test_non_png_paths_refuse_before_data_and_never_get_rewritten(self):
        for field in ('filepath', 'filepath_raw'):
            with self.subTest(field=field):
                a = self.image(field); setattr(a, field, 'source.vtf'); row = ticket(a)
                self.refused([row]); self.assertEqual(getattr(a, field), 'source.vtf')
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))
        self.no_buffers()

    def test_acquired_dimensions_must_match_admitted_header(self):
        a = self.image(); row = ticket(a); a.dimensions = (9, 4)
        error = self.refused([row])
        self.assertEqual(error.code, 'ACQUIRED_IMAGE_DIMENSIONS_DIFFER')
        self.assertEqual(error.summary['size_getter_attempts'], 1)
        self.assertEqual(error.summary['channel_getter_attempts'], 0)

    def test_channels_bool_or_other_channel_count_refuses(self):
        for channels in (True, 1, 2, 5):
            with self.subTest(channels=channels):
                a = self.image(str(channels)); a.channel_count = channels
                self.refused([ticket(a)])

    def test_size_that_does_not_produce_loaded_buffer_refuses(self):
        a = self.image(); a.load_on_size = False
        error = self.refused([ticket(a)])
        self.assertEqual(error.code, 'IMAGE_BUFFER_STILL_UNAVAILABLE')

    def test_acquisition_metadata_change_is_not_accepted_as_cache_transition(self):
        a = self.image(); a.on_size = lambda image: setattr(image, 'alpha_mode', 'PREMUL')
        error = self.refused([ticket(a)])
        self.assertEqual(error.code, 'METADATA_CHANGED_DURING_ACQUISITION')

    def test_acquisition_packed_pointer_drift_refuses(self):
        a = self.image(); a.on_size = lambda image: setattr(image, 'packed_pointer', image.packed_pointer + 99)
        self.refused([ticket(a)])

    def test_acquisition_packed_byte_change_refuses_even_with_same_dimensions(self):
        a = self.image(); a.on_size = lambda image: setattr(image, 'raw', png(8, 4, 2))
        error = self.refused([ticket(a)])
        self.assertEqual(error.code, 'INSPECTED_PACKED_HASH_CHANGED')

    def test_caller_pin_mutation_cannot_move_the_expected_hash_during_getter(self):
        a = self.image(); row = ticket(a)
        def mutate(image):
            image.raw = png(8, 4, 2)
            row['encoded_sha256'] = hashlib.sha256(image.raw).hexdigest()
        a.on_size = mutate
        error = self.refused([row])
        self.assertEqual(error.code, 'INSPECTED_PACKED_HASH_CHANGED')

    def test_last_image_getter_cannot_silently_change_an_earlier_image(self):
        a, b = self.image('a'), self.image('b')
        b.on_size = lambda image: setattr(a, 'filepath_raw', 'changed.png')
        error = self.refused([ticket(a), ticket(b)])
        self.assertEqual(error.code, 'METADATA_CHANGED_DURING_ACQUISITION')

    def test_raising_size_getter_retains_honest_attempt_counts_and_safe_refusal(self):
        def fail(image): raise RuntimeError('private image name must not escape')
        a = self.image(); a.on_size = fail
        error = self.refused([ticket(a)])
        self.assertEqual(error.code, 'PACKED_IMAGE_READINESS_API_OR_ACQUISITION_FAILED')
        self.assertEqual(error.summary['size_getter_attempts'], 1)
        self.assertTrue(error.summary['image_buffer_getters_used'])
        self.assertNotIn('private image name', str(error.summary))

    def test_malformed_ticket_or_owner_key_refuses_without_attribute_fallback(self):
        class ForeignKey:
            def __eq__(self, other): raise AssertionError('foreign key comparison touched')
        a = self.image(); row = ticket(a)
        bad = dict(row); bad['packed_key'] = ForeignKey()
        self.refused([bad]); self.no_buffers()
        bad = dict(row); bad['extra'] = True
        self.refused([bad]); self.no_buffers()

    def test_invalid_digest_and_non_integer_dimensions_refuse_before_data(self):
        a = self.image(); row = ticket(a)
        for field, value in (('encoded_sha256', 'G' * 64), ('width', True), ('encoded_bytes', True)):
            with self.subTest(field=field):
                bad = dict(row); bad[field] = value
                self.refused([bad]); self.no_buffers()
        self.assertFalse(any(kind == 'packed_data' for kind, _ in self.events))

    def test_empty_image_set_has_no_getter_or_export_claim(self):
        actual, summary = C.acquire_packed_png_buffers(BPY, (), I)
        self.assertEqual(actual, [])
        self.assertEqual(summary['images_admitted'], 0)
        self.assertFalse(summary['image_buffer_getters_used'])
        self.assertEqual(self.events, [])
        self.assertFalse(summary['exporter_qualified'])


if __name__ == '__main__':
    unittest.main()
