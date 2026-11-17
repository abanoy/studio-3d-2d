"""One passive call before the sealed oracle's original count guard; exact inverse."""
import hashlib

ORACLE_SHA256 = 'f1dfc3a37c32c1c8b57537b1500b701792df13e4e8b87abe13b0ce49be2c4cec'
ORACLE_BYTES = 14055
INDEX_SHA256 = 'd27d9873bc08ec2bc37f8939ae09f9b071f9f4e6fda8b112a2626fef7fabbb45'
ANCHOR = b"        require(0 <= count <= getattr(self.limits, name + '_count'), 'oracle table-count budget')\n"
INSERT = b"        _observe_table_count(name, count, getattr(self.limits, name + '_count'), token['start'])\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def instrument_source(raw):
    if type(raw) is not bytes or len(raw) != ORACLE_BYTES or sha(raw) != ORACLE_SHA256:
        raise ValueError('exact sealed oracle source required')
    if raw.count(ANCHOR) != 1 or INSERT in raw:
        raise ValueError('exact unique count guard required')
    patched = raw.replace(ANCHOR, INSERT + ANCHOR, 1)
    if restore_source(patched) != raw:
        raise ValueError('instrumentation inverse differs')
    return patched


def restore_source(raw):
    if type(raw) is not bytes or raw.count(INSERT + ANCHOR) != 1:
        raise ValueError('exact one-call instrumented oracle required')
    restored = raw.replace(INSERT + ANCHOR, ANCHOR, 1)
    if len(restored) != ORACLE_BYTES or sha(restored) != ORACLE_SHA256:
        raise ValueError('instrumentation inverse does not restore pinned source')
    return restored
