"""CPU-only exact forward/inverse of the declared parent source edits."""
import hashlib


def render(raw, row, inverse=False):
    source_key, target_key = ('new_sha256', 'old_sha256') if inverse else ('old_sha256', 'new_sha256')
    if hashlib.sha256(raw).hexdigest() != row[source_key]: raise ValueError('Exact source delta input required')
    source = raw.decode('utf-8'); pieces = []; position = 0
    for operation in row['operations']:
        start = operation['new_start' if inverse else 'old_start']
        before = operation['after' if inverse else 'before']
        after = operation['before' if inverse else 'after']
        if start < position or source[start:start + len(before)] != before:
            raise ValueError('Exact nonoverlapping source operation required')
        pieces.extend((source[position:start], after)); position = start + len(before)
    pieces.append(source[position:]); result = ''.join(pieces).encode('utf-8')
    if hashlib.sha256(result).hexdigest() != row[target_key]: raise ValueError('Exact source delta output required')
    return result
