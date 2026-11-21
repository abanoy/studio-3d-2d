"""Explicit bounded packed-PNG buffer acquisition for one owned export host.

No bpy import, I/O, pixels getter, reload, unpack, metadata edit or exporter.
Root authenticates bpy/types, inspector5efd, private tickets and the owned job.
The host rechecks graph/material/Library references before AND after this call.
The source-level packed branch is not a universal no-C-I/O or cache provenance
proof. Frozen shared73 remains unchanged and validates the returned tickets.
"""
import hashlib
import json

MAX_IMAGES = 128
MAX_ENCODED_BYTES = MAX_DECODED_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = MAX_TOTAL_DECODED_BYTES = 128 * 1024 * 1024
PRIVATE_FIELDS = frozenset(('image', 'packed_part', 'packed', 'name', 'filepath',
    'encoded_bytes', 'encoded_sha256', 'width', 'height', 'packed_part_key', 'packed_key'))
_ANIMATION_ATTRIBUTE_MISSING = object()
_PUBLIC_API_ATTRIBUTES = frozenset(('types', 'Image', 'UDIMTile', 'ImagePackedFile', 'PackedFile',
    'original', 'library', 'as_pointer', 'source', 'type', 'is_dirty', 'animation_data', 'name',
    'filepath', 'filepath_raw', 'is_multiview', 'use_multiview', 'tiles', 'number', 'packed_files',
    'packed_file', 'view', 'tile_number', 'size', 'data', 'alpha_mode', 'colorspace_settings',
    'id_data', 'has_data', 'channels'))
_SAFE_EXCEPTION_TYPES = {AttributeError: 'AttributeError', TypeError: 'TypeError',
    ValueError: 'ValueError', KeyError: 'KeyError', IndexError: 'IndexError',
    RuntimeError: 'RuntimeError', OverflowError: 'OverflowError', MemoryError: 'MemoryError'}


class Refusal(ValueError):
    def __init__(self, code, summary=None):
        super().__init__(code)
        self.code = code
        self.summary = None if summary is None else dict(summary)


def _need(ok, code):
    if not ok:
        raise Refusal(code)


def _text(value, limit):
    _need(type(value) is str and len(value) <= limit and '\x00' not in value,
          'BOUNDED_IMAGE_METADATA_REQUIRED')
    return value


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _structure(row, types, inspector):
    """Nonloading fields only; returned wrappers keep actual owners alive."""
    image = row['image']
    _need(type(image) is types.Image and image.original is image and image.library is None,
          'GENUINE_LOCAL_ORIGINAL_IMAGE_REQUIRED')
    pointer = image.as_pointer()
    _need(type(pointer) is int and 0 < pointer < 2**64, 'IMAGE_POINTER_REQUIRED')
    # Pinned Image RNA exposes no animation_data: its IDTypeInfo has
    # IDTYPE_FLAGS_NO_ANIMDATA. The reserved DNA adt slot is not an RNA property.
    # An exposed non-None value remains refused, rather than silently ignored.
    animation = getattr(image, 'animation_data', _ANIMATION_ATTRIBUTE_MISSING)
    animation_present = animation is not _ANIMATION_ATTRIBUTE_MISSING
    _need(image.source == 'FILE' and image.type == 'IMAGE' and image.is_dirty is False and
          (not animation_present or animation is None), 'CLEAN_NONANIMATED_FILE_IMAGE_REQUIRED')
    name = _text(image.name, 256)
    filepath = _text(image.filepath, 4096)
    filepath_raw = _text(image.filepath_raw, 4096)
    _need(name == row['name'] and filepath == row['filepath'], 'INSPECTED_IMAGE_METADATA_CHANGED')
    _need(all(path == '' or path.casefold().endswith('.png') for path in (filepath, filepath_raw)),
          'PACKED_PNG_AUTO_MIME_PATH_CONFLICT')
    _need(image.is_multiview is False and image.use_multiview is False,
          'MULTIVIEW_IMAGE_REFUSED')
    _need(len(image.tiles) == 1, 'EXACT_SINGLE_TILE_REQUIRED')
    tiles = tuple(image.tiles)
    _need(len(tiles) == 1, 'EXACT_SINGLE_TILE_REQUIRED')
    tile = tiles[0]
    tile_key = inspector._nonid_key(tile, types.UDIMTile, image)
    _need(type(tile.number) is int and tile.number == 1001, 'EXACT_DEFAULT_TILE_REQUIRED')
    _need(len(image.packed_files) == 1, 'EXACT_SINGLE_PACKED_ENTRY_REQUIRED')
    parts = tuple(image.packed_files)
    _need(len(parts) == 1, 'EXACT_SINGLE_PACKED_ENTRY_REQUIRED')
    part = parts[0]
    part_key = inspector._nonid_key(part, types.ImagePackedFile, image)
    packed = image.packed_file
    packed_key = inspector._nonid_key(packed, types.PackedFile, image)
    _need(part_key == row['packed_part_key'] and packed_key == row['packed_key'] and
          inspector._nonid_key(row['packed_part'], types.ImagePackedFile, image) == part_key and
          inspector._nonid_key(row['packed'], types.PackedFile, image) == packed_key and
          inspector._nonid_key(part.packed_file, types.PackedFile, image) == packed_key,
          'INSPECTED_PACKED_OWNER_OR_POINTER_CHANGED')
    _need(type(part.view) is int and part.view == 0 and
          type(part.tile_number) is int and part.tile_number == 1001,
          'EXACT_PACKED_VIEW_AND_TILE_REQUIRED')
    part_path = _text(part.filepath, 4096)
    count = packed.size
    _need(type(count) is int and 33 <= count <= MAX_ENCODED_BYTES and count == row['encoded_bytes'],
          'PACKED_ENCODED_SIZE_OR_TICKET_CHANGED')
    alpha_mode = _text(image.alpha_mode, 64)
    colorspace = _text(image.colorspace_settings.name, 256)
    metadata = (pointer, name, filepath, filepath_raw, image.source, image.type,
                image.is_dirty, alpha_mode, colorspace, tile_key, part_key, packed_key,
                part_path, part.view, part.tile_number, count, animation_present)
    return dict(image=image, tile=tile, part=part, packed=packed, metadata=metadata,
                animation_attribute_present=animation_present)


def _payload(row, observed, inspector):
    raw = observed['packed'].data
    _need(type(raw) is bytes and len(raw) == row['encoded_bytes'], 'EXACT_PACKED_BYTES_REQUIRED')
    _need(hashlib.sha256(raw).hexdigest() == row['encoded_sha256'], 'INSPECTED_PACKED_HASH_CHANGED')
    width, height = inspector._png(raw)
    _need(type(width) is int and type(height) is int and
          (width, height) == (row['width'], row['height']) and
          width * height * 16 <= MAX_DECODED_BYTES, 'INSPECTED_PNG_DIMENSIONS_CHANGED')
    return width * height * 16


def acquire_packed_png_buffers(bpy, private_images_tuple, inspection_module):
    """Return (shared73 tickets, safe summary), or Refusal with safe summary.

    All encoded sizes, hashes, headers and aggregate prospective budgets are
    admitted before the first image.size/channels getter. Only an expected
    loaded-cache transition is allowed; nonbuffer metadata is rechecked.
    """
    summary = dict(format='has_bounded_packed_png_buffer_readiness_1', status='REFUSED',
        images_admitted=0, encoded_bytes=0, prospective_rgba_f32_bytes=0,
        complete_set_admitted_before_buffer_getters=False,
        packed_memory_branch_preconditions_validated=False,
        image_buffer_getters_used=False, size_getter_attempts=0, channel_getter_attempts=0,
        images_without_animation_data_attribute=0, images_with_exposed_empty_animation_data=0,
        initially_loaded_images=0, initially_unloaded_images=0, images_verified_ready=0,
        nonbuffer_metadata_and_packed_refs_unchanged=False, packed_hashes_rechecked=False,
        python_image_pixels_getter_used=False, python_image_foreach_get_used=False,
        C_encoded_image_decode_may_occur=True, C_external_access_absence_proven=False,
        cached_pixel_provenance_qualified=False, metadata_written=False,
        resource_equivalence_qualified=False, normal_fidelity_qualified=False,
        native_or_historical_point_identity_qualified=False, exporter_qualified=False,
        application_adoption_qualified=False)
    phase, image_ordinal = 'REQUEST_TICKETS', None
    try:
        _need(type(private_images_tuple) is tuple and len(private_images_tuple) <= MAX_IMAGES,
              'BOUNDED_PRIVATE_IMAGE_TUPLE_REQUIRED')
        # Freeze every expected scalar/key before any genuine image getter can
        # run. Retain actual references, never mutable caller expectation dicts.
        frozen_rows = []
        for row in private_images_tuple:
            _need(type(row) is dict and set(row) == PRIVATE_FIELDS, 'EXACT_PRIVATE_INSPECTION_TICKET_REQUIRED')
            frozen_rows.append(dict(row))
        phase = 'RNA_TYPES'
        types = bpy.types
        admitted, total = [], 0
        for image_ordinal, row in enumerate(frozen_rows):
            phase = 'TICKET_ADMISSION'
            _text(row['name'], 256)
            _text(row['filepath'], 4096)
            _need(type(row['encoded_sha256']) is str and len(row['encoded_sha256']) == 64 and
                  all(c in '0123456789abcdef' for c in row['encoded_sha256']), 'INSPECTED_SHA256_REQUIRED')
            _need(type(row['encoded_bytes']) is int and 33 <= row['encoded_bytes'] <= MAX_ENCODED_BYTES and
                  type(row['width']) is int and type(row['height']) is int and
                  0 < row['width'] <= 16384 and 0 < row['height'] <= 16384 and
                  row['width'] * row['height'] * 16 <= MAX_DECODED_BYTES,
                  'BOUNDED_INSPECTION_DIMENSIONS_AND_SIZE_REQUIRED')
            for key_name, expected in (('packed_part_key', types.ImagePackedFile), ('packed_key', types.PackedFile)):
                key = row[key_name]
                _need(type(key) is tuple and len(key) == 3 and key[0] is expected and
                      type(key[1]) is int and key[1] == id(row['image']) and
                      type(key[2]) is int and 0 < key[2] < 2**64,
                      'EXACT_INSPECTED_OWNER_POINTER_KEY_REQUIRED')
            _need(all(row['image'] is not prior[0]['image'] for prior in admitted),
                  'DUPLICATE_ACTUAL_IMAGE_TICKET')
            phase = 'IMAGE_STRUCTURE'
            observed = _structure(row, types, inspection_module)
            phase = 'ENCODED_SET_BUDGET'
            total += row['encoded_bytes']
            _need(total <= MAX_TOTAL_BYTES, 'AGGREGATE_ENCODED_BUDGET')
            admitted.append((row, observed))
        summary['images_admitted'] = len(admitted)
        summary['encoded_bytes'] = total
        summary['images_without_animation_data_attribute'] = sum(
            not observed['animation_attribute_present'] for _, observed in admitted)
        summary['images_with_exposed_empty_animation_data'] = sum(
            observed['animation_attribute_present'] for _, observed in admitted)
        prospective = 0
        # All packed sizes above precede the first packed data getter; all
        # payloads and prospective budgets below precede any buffer getter.
        for image_ordinal, (row, observed) in enumerate(admitted):
            phase = 'PACKED_PNG_ADMISSION'
            prospective += _payload(row, observed, inspection_module)
            _need(prospective <= MAX_TOTAL_DECODED_BYTES, 'AGGREGATE_PROSPECTIVE_RGBA_F32_BUDGET')
        summary['prospective_rgba_f32_bytes'] = prospective
        # A payload getter must not silently invalidate another admitted row.
        for image_ordinal, (row, observed) in enumerate(admitted):
            phase = 'PRE_ACQUISITION_RECHECK'
            current = _structure(row, types, inspection_module)
            _need(current['metadata'] == observed['metadata'], 'METADATA_CHANGED_BEFORE_ACQUISITION')
        summary['complete_set_admitted_before_buffer_getters'] = True
        summary['packed_memory_branch_preconditions_validated'] = True
        for image_ordinal, (row, observed) in enumerate(admitted):
            phase = 'LOADED_STATE_OBSERVATION'
            image = observed['image']
            loaded = image.has_data
            _need(type(loaded) is bool, 'BOOLEAN_LOADED_CACHE_STATE_REQUIRED')
            summary['initially_loaded_images' if loaded else 'initially_unloaded_images'] += 1
            summary['image_buffer_getters_used'] = True
            summary['size_getter_attempts'] += 1
            phase = 'IMAGE_SIZE_ACQUISITION'
            actual_size = tuple(image.size)
            _need(len(actual_size) == 2 and all(type(v) is int for v in actual_size) and
                  actual_size == (row['width'], row['height']), 'ACQUIRED_IMAGE_DIMENSIONS_DIFFER')
            summary['channel_getter_attempts'] += 1
            phase = 'IMAGE_CHANNELS_ACQUISITION'
            channels = image.channels
            _need(type(channels) is int and channels in (3, 4), 'ACQUIRED_IMAGE_CHANNELS_DIFFER')
            phase = 'LOADED_STATE_RECHECK'
            _need(image.has_data is True, 'IMAGE_BUFFER_STILL_UNAVAILABLE')
        # Cross-image changes during the last getter must be detected too.
        for image_ordinal, (row, observed) in enumerate(admitted):
            phase = 'POST_ACQUISITION_RECHECK'
            current = _structure(row, types, inspection_module)
            _need(current['metadata'] == observed['metadata'], 'METADATA_CHANGED_DURING_ACQUISITION')
            phase = 'POST_PACKED_PNG_RECHECK'
            _payload(row, current, inspection_module)
            _need(current['image'].has_data is True, 'IMAGE_BUFFER_LOST_DURING_RECHECK')
            summary['images_verified_ready'] += 1
        summary['nonbuffer_metadata_and_packed_refs_unchanged'] = True
        summary['packed_hashes_rechecked'] = True
        phase = 'FINAL_SUMMARY'
        summary['packed_header_set_sha256'] = _digest([(row['encoded_sha256'], row['encoded_bytes'],
            row['width'], row['height']) for row, _ in admitted])
        summary['status'] = 'BOUNDED_PACKED_PNG_BUFFERS_READY_1'
        tickets = [dict(image=row['image'], packed_sha256=row['encoded_sha256'],
                        encoded_bytes=row['encoded_bytes']) for row, _ in admitted]
        return tickets, summary
    except Exception as error:
        code = error.code if type(error) is Refusal else 'PACKED_IMAGE_READINESS_API_OR_ACQUISITION_FAILED'
        summary['refusal'] = code
        summary['failure_phase'] = phase
        summary['failure_image_ordinal'] = image_ordinal
        summary['failure_exception_type'] = 'Refusal' if type(error) is Refusal else _SAFE_EXCEPTION_TYPES.get(type(error), 'OtherError')
        # AttributeError.name is emitted only for this fixed public API set.
        # Never copy exception messages, object reprs, filenames or values.
        attribute = error.name if type(error) is AttributeError else None
        summary['failure_attribute'] = attribute if type(attribute) is str and attribute in _PUBLIC_API_ATTRIBUTES else None
        raise Refusal(code, summary) from error
