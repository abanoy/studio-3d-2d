"""Pure classification of genuine private-desktop receipt inventories.

The caller hashes the actual receipt bytes and inventories BOTH ROOT/output and
ROOT/experiments before launch and afterward. This module does no file IO and
does not certify a receipt's physical flags. New desktop duplicates remain for
the coordinator's independent physical-field comparison and deduplication.
"""
import copy
import json
from pathlib import PurePosixPath

MAX_ROWS = 100_000
MAX_PATH = 4096
MAX_DESKTOP = 256
FORMAT = 'studio_private_desktop_1'


def _need(value, message):
    if not value:
        raise ValueError(message)


def _rows(rows):
    _need(type(rows) is list and len(rows) <= MAX_ROWS, 'Bounded receipt row list required')
    result = {}
    conflicts = []
    for row in rows:
        _need(type(row) is dict and set(row) == {'path', 'sha256', 'value'}, 'Exact receipt row schema required')
        path, digest, value = row['path'], row['sha256'], row['value']
        _need(type(path) is str and 0 < len(path) <= MAX_PATH and '\\' not in path and ':' not in path,
              'Bounded root-relative POSIX receipt path required')
        parsed = PurePosixPath(path)
        _need(not parsed.is_absolute() and '..' not in parsed.parts and parsed.as_posix() == path
              and (path.startswith('output/') or path.startswith('experiments/')),
              'Receipt path must be inside output/ or experiments/')
        _need(type(digest) is str and len(digest) == 64 and all(ch in '0123456789abcdef' for ch in digest),
              'Exact lowercase SHA256 required')
        _need(type(value) is dict and value.get('format') == FORMAT,
              'Genuine private-desktop receipt format required')
        desktop = value.get('desktop')
        _need(type(desktop) is str and 0 < len(desktop) <= MAX_DESKTOP, 'Bounded desktop identity required')
        try:
            payload = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError('Receipt value must be finite JSON data') from error
        if path in result:
            previous = result[path]
            if (previous['sha256'], previous['payload']) != (digest, payload):
                conflicts.append({'kind': 'conflicting_inventory_path', 'path': path,
                                  'first_sha256': previous['sha256'], 'other_sha256': digest,
                                  'first_desktop': previous['value']['desktop'], 'other_desktop': desktop})
            continue
        # Copy JSON data so neither caller mutations nor returned-row mutations
        # can change the other inventory. No original caller dictionary is edited.
        result[path] = {'path': path, 'sha256': digest, 'value': copy.deepcopy(value), 'payload': payload}
    return result, conflicts


def _public_row(row):
    return {'path': row['path'], 'sha256': row['sha256'], 'value': copy.deepcopy(row['value'])}


def classify(prior_rows, after_rows):
    """Return current, archived_copies, conflicts and changed_original_archives.

    Only an exact prior SHA for that desktop admits an inherited copy. Same-ID
    unknown bytes are a conflict, never an exclusion. Prior experiments receipts
    must remain present and unchanged at the same source paths. Prior output
    receipts may disappear or be overwritten by a genuinely new desktop.

    Exact duplicate inventory rows at one path are idempotent. Distinct paths for
    a new desktop are all returned in current, even if their byte hashes differ:
    the caller must compare physical fields before deduplicating those jobs.
    Partial genuine receipts also remain current so missing closure flags fail
    the caller's physical audit rather than disappearing from it.
    """
    prior, prior_conflicts = _rows(prior_rows)
    after, after_conflicts = _rows(after_rows)
    conflicts = [dict(row, inventory='prior') for row in prior_conflicts]
    conflicts += [dict(row, inventory='after') for row in after_conflicts]
    known = {}
    for row in prior.values():
        known.setdefault(row['value']['desktop'], {}).setdefault(row['sha256'], []).append(row)
    current, copies, unchanged, changed = [], [], [], []
    for path, before in prior.items():
        if not path.startswith('experiments/'):
            continue
        found = after.get(path)
        if found is None:
            changed.append({'kind': 'missing', 'path': path, 'before_sha256': before['sha256'], 'after_sha256': None})
        elif (found['sha256'], found['payload']) != (before['sha256'], before['payload']):
            changed.append({'kind': 'changed', 'path': path, 'before_sha256': before['sha256'], 'after_sha256': found['sha256']})
    for path, row in after.items():
        previous = prior.get(path)
        if previous and (row['sha256'], row['payload']) == (previous['sha256'], previous['payload']):
            unchanged.append(path)
            continue
        if path.startswith('experiments/'):
            if previous is None:
                changed.append({'kind': 'added', 'path': path, 'before_sha256': None, 'after_sha256': row['sha256']})
            # Original archive mutation/membership drift is not a new job.
            # A preserved copy elsewhere cannot conceal this source drift.
            continue
        desktop = row['value']['desktop']
        desktop_sources = known.get(desktop)
        if desktop_sources is None:
            current.append(_public_row(row))
            continue
        sources = desktop_sources.get(row['sha256'])
        if sources is None:
            conflicts.append({'kind': 'prior_desktop_unknown_bytes', 'path': path, 'desktop': desktop,
                              'after_sha256': row['sha256'], 'known_prior_sha256': sorted(desktop_sources),
                              'prior_paths': sorted(item['path'] for values in desktop_sources.values() for item in values)})
            continue
        if any(item['payload'] != row['payload'] for item in sources):
            conflicts.append({'kind': 'same_sha_payload_differs', 'path': path, 'desktop': desktop,
                              'sha256': row['sha256'], 'prior_paths': sorted(item['path'] for item in sources)})
            continue
        proof = [{'path': item['path'], 'sha256': item['sha256']}
                 for item in sorted(sources, key=lambda item: item['path'])]
        copies.append({'path': path, 'sha256': row['sha256'], 'desktop': desktop,
                       'prior_originals': proof,
                       'source_archive_paths': [item['path'] for item in proof if item['path'].startswith('experiments/')],
                       'previous_path_sha256': previous['sha256'] if previous else None})
    return {'current': current, 'archived_copies': copies, 'conflicts': conflicts,
            'changed_original_archives': changed, 'unchanged_prior_paths': sorted(unchanged)}
